"""Generate a seeded random ITCH-style stream plus the golden expected output.

Usage:
    python3 model/gen_vectors.py --n 2000 --seed 1 --out vectors/random_1

Writes:
    <out>.bin       raw back-to-back messages
    <out>.hex       same stream as 64-bit big-endian beats, one hex word per line
                    (last beat zero-padded) for $readmemh in the testbench
    <out>.exp.csv   expected top-of-book after every book-touching message
"""
import argparse
import csv
import os
import random

import itch

STOCKS = ["AAPL", "MSFT", "NVDA", "IMC"]


def generate(n: int, seed: int) -> bytes:
    rng = random.Random(seed)
    live = {}  # ref -> (shares)
    next_ref = 1
    ts = 0
    out = bytearray()
    for _ in range(n):
        ts += rng.randint(1, 5000)
        choice = rng.random()
        if not live or choice < 0.45:
            ref = next_ref
            next_ref += 1
            shares = rng.randint(1, 500)
            out += itch.encode_add(
                ts, ref, rng.choice("BS"), shares, rng.choice(STOCKS), rng.randint(9900, 10100)
            )
            live[ref] = shares
            continue
        ref = rng.choice(list(live))
        if choice < 0.65:  # partial execute
            sh = rng.randint(1, live[ref])
            out += itch.encode_exec(ts, ref, sh, ts)
            live[ref] -= sh
        elif choice < 0.80:  # partial cancel
            sh = rng.randint(1, live[ref])
            out += itch.encode_cancel(ts, ref, sh)
            live[ref] -= sh
        elif choice < 0.92:  # delete
            out += itch.encode_delete(ts, ref)
            live[ref] = 0
        else:  # replace
            new_ref = next_ref
            next_ref += 1
            shares = rng.randint(1, 500)
            out += itch.encode_replace(ts, ref, new_ref, shares, rng.randint(9900, 10100))
            live[ref] = 0
            live[new_ref] = shares
        live = {r: s for r, s in live.items() if s > 0}
    return bytes(out)


def write_hex(data: bytes, path: str) -> None:
    padded = data + b"\x00" * (-len(data) % 8)
    with open(path, "w") as f:
        for i in range(0, len(padded), 8):
            f.write(padded[i : i + 8].hex() + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="vectors/random_1")
    a = ap.parse_args()

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    data = generate(a.n, a.seed)
    with open(a.out + ".bin", "wb") as f:
        f.write(data)
    write_hex(data, a.out + ".hex")
    with open(a.out + ".exp.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["msg_index", "stock", "bid_px", "bid_qty", "ask_px", "ask_qty"])
        w.writerows(itch.run(data))
    print(f"wrote {len(data)} bytes, {a.n} messages -> {a.out}.*")


if __name__ == "__main__":
    main()
