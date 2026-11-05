# ITCH subset used in v1

Raw back-to-back messages, no Ethernet/IP/UDP/MoldUDP64 framing. All fields big-endian.
Verify every offset against the official *Nasdaq TotalView-ITCH 5.0* specification.

Common header (11 bytes): type (1), stock locate (2), tracking number (2), timestamp (6).

| Type | Name            | Len | Fields after header (offset from msg start)                                 |
|------|-----------------|-----|------------------------------------------------------------------------------|
| `A`  | Add Order       | 36  | order ref (11, 8B), side B/S (19, 1B), shares (20, 4B), stock (24, 8B), price (32, 4B) |
| `E`  | Order Executed  | 31  | order ref (11, 8B), executed shares (19, 4B), match number (23, 8B)          |
| `X`  | Order Cancel    | 23  | order ref (11, 8B), cancelled shares (19, 4B)                                |
| `D`  | Order Delete    | 19  | order ref (11, 8B)                                                           |
| `U`  | Order Replace   | 35  | original ref (11, 8B), new ref (19, 8B), shares (27, 4B), price (31, 4B)     |

Later: `F` (Add with MPID, 40 B), MoldUDP64 framing (20 B header + 2-byte length prefix per message).

## Hardware notes
- Input: 64-bit AXI-Stream. Messages are not beat-aligned, so the parser needs a byte-shift/alignment stage.
- Target: 1 beat per cycle, no stalls on valid input.
