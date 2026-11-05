"""Golden model: ITCH-style message codec and order book.

Message layouts follow Nasdaq TotalView-ITCH 5.0 (big-endian). Verify offsets
against the official spec before relying on them (see docs/itch_subset.md).
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Tuple

# type -> total message length in bytes
MSG_LEN = {b"A": 36, b"E": 31, b"X": 23, b"D": 19, b"U": 35}

HEADER = struct.Struct(">cHH6s")  # type, stock locate, tracking, timestamp (11 B)


def _ts(ts: int) -> bytes:
    return ts.to_bytes(6, "big")


def encode_add(ts, ref, side, shares, stock, price, locate=0, tracking=0) -> bytes:
    stock_b = stock.encode().ljust(8, b" ")
    return (
        HEADER.pack(b"A", locate, tracking, _ts(ts))
        + struct.pack(">Qc", ref, side.encode())
        + struct.pack(">I", shares)
        + stock_b
        + struct.pack(">I", price)
    )


def encode_exec(ts, ref, shares, match, locate=0, tracking=0) -> bytes:
    return HEADER.pack(b"E", locate, tracking, _ts(ts)) + struct.pack(">QIQ", ref, shares, match)


def encode_cancel(ts, ref, shares, locate=0, tracking=0) -> bytes:
    return HEADER.pack(b"X", locate, tracking, _ts(ts)) + struct.pack(">QI", ref, shares)


def encode_delete(ts, ref, locate=0, tracking=0) -> bytes:
    return HEADER.pack(b"D", locate, tracking, _ts(ts)) + struct.pack(">Q", ref)


def encode_replace(ts, old_ref, new_ref, shares, price, locate=0, tracking=0) -> bytes:
    return HEADER.pack(b"U", locate, tracking, _ts(ts)) + struct.pack(
        ">QQII", old_ref, new_ref, shares, price
    )


@dataclass
class Msg:
    kind: str
    ts: int
    ref: int = 0
    side: str = ""
    shares: int = 0
    stock: str = ""
    price: int = 0
    new_ref: int = 0


def parse_stream(data: bytes) -> Iterator[Msg]:
    """Split a raw back-to-back message stream into Msg objects."""
    i = 0
    while i < len(data):
        t = data[i : i + 1]
        if t not in MSG_LEN:
            raise ValueError(f"unknown message type {t!r} at offset {i}")
        n = MSG_LEN[t]
        body = data[i : i + n]
        if len(body) != n:
            raise ValueError(f"truncated message at offset {i}")
        _, _, _, ts = HEADER.unpack_from(body, 0)
        ts = int.from_bytes(ts, "big")
        if t == b"A":
            ref, side = struct.unpack_from(">Qc", body, 11)
            (shares,) = struct.unpack_from(">I", body, 20)
            stock = body[24:32].decode().rstrip()
            (price,) = struct.unpack_from(">I", body, 32)
            yield Msg("A", ts, ref, side.decode(), shares, stock, price)
        elif t == b"E":
            ref, shares, _match = struct.unpack_from(">QIQ", body, 11)
            yield Msg("E", ts, ref, shares=shares)
        elif t == b"X":
            ref, shares = struct.unpack_from(">QI", body, 11)
            yield Msg("X", ts, ref, shares=shares)
        elif t == b"D":
            (ref,) = struct.unpack_from(">Q", body, 11)
            yield Msg("D", ts, ref)
        elif t == b"U":
            old, new, shares, price = struct.unpack_from(">QQII", body, 11)
            yield Msg("U", ts, old, shares=shares, price=price, new_ref=new)
        i += n


# --------------------------------------------------------------------------
# Order book
# --------------------------------------------------------------------------
@dataclass
class _Order:
    stock: str
    side: str
    shares: int
    price: int


class OrderBook:
    """Per-symbol price-level book with best bid/ask queries."""

    def __init__(self) -> None:
        self.orders: Dict[int, _Order] = {}
        # stock -> side -> price -> total shares
        self.levels: Dict[str, Dict[str, Dict[int, int]]] = {}

    def _lvl(self, stock: str, side: str) -> Dict[int, int]:
        return self.levels.setdefault(stock, {"B": {}, "S": {}})[side]

    def _add(self, ref: int, o: _Order) -> None:
        self.orders[ref] = o
        lv = self._lvl(o.stock, o.side)
        lv[o.price] = lv.get(o.price, 0) + o.shares

    def _reduce(self, ref: int, shares: int) -> Optional[_Order]:
        o = self.orders.get(ref)
        if o is None:
            return None
        shares = min(shares, o.shares)
        lv = self._lvl(o.stock, o.side)
        lv[o.price] -= shares
        if lv[o.price] == 0:
            del lv[o.price]
        o.shares -= shares
        if o.shares == 0:
            del self.orders[ref]
        return o

    def apply(self, m: Msg) -> Optional[str]:
        """Apply a message; return the affected stock (None if ignored)."""
        if m.kind == "A":
            self._add(m.ref, _Order(m.stock, m.side, m.shares, m.price))
            return m.stock
        if m.kind in ("E", "X"):
            o = self._reduce(m.ref, m.shares)
            return o.stock if o else None
        if m.kind == "D":
            o = self.orders.get(m.ref)
            if o is None:
                return None
            self._reduce(m.ref, o.shares)
            return o.stock
        if m.kind == "U":
            o = self.orders.get(m.ref)
            if o is None:
                return None
            stock, side = o.stock, o.side
            self._reduce(m.ref, o.shares)
            self._add(m.new_ref, _Order(stock, side, m.shares, m.price))
            return stock
        raise ValueError(m.kind)

    def top(self, stock: str) -> Tuple[int, int, int, int]:
        """(bid_px, bid_qty, ask_px, ask_qty); 0/0 when a side is empty."""
        lv = self.levels.get(stock, {"B": {}, "S": {}})
        bpx = max(lv["B"]) if lv["B"] else 0
        apx = min(lv["S"]) if lv["S"] else 0
        return bpx, lv["B"].get(bpx, 0), apx, lv["S"].get(apx, 0)


def run(data: bytes) -> List[Tuple[int, str, int, int, int, int]]:
    """Run a stream; one output row per message that touched a book:
    (msg_index, stock, bid_px, bid_qty, ask_px, ask_qty)."""
    book = OrderBook()
    out = []
    for idx, m in enumerate(parse_stream(data)):
        stock = book.apply(m)
        if stock is not None:
            out.append((idx, stock, *book.top(stock)))
    return out
