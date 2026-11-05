# itch-orderbook-fpga

Low-latency market-data pipeline on FPGA (Verilog): an ITCH-style message parser feeding a
top-of-book order book, verified against a Python golden model.

> **Status:** work in progress. Python golden model and vector generator are done; RTL is next.

## Pipeline

```
byte stream (AXI-Stream, 64-bit)
   -> parser (alignment + message decode)
   -> order book (per-symbol best bid/ask)
   -> trigger (optional: spread below threshold)
```

## Repo layout

| Path        | Contents                                                        |
|-------------|-----------------------------------------------------------------|
| `model/`    | Python golden model (`itch.py`) and test-vector generator       |
| `rtl/`      | Verilog sources                                                 |
| `tb/`       | Self-checking testbenches                                       |
| `tests/`    | Python tests for the golden model                               |
| `vectors/`  | Generated streams and expected outputs (git-ignored)           |
| `docs/`     | Message-format notes, architecture diagrams                     |
| `scripts/`  | Vivado / simulation scripts                                     |

## Quick start

```bash
python3 -m unittest discover -s tests          # golden model tests
python3 model/gen_vectors.py --n 2000 --seed 1 --out vectors/random_1
```

## Results (fill in as you go)

| Metric                          | Parser | Order book | Total |
|---------------------------------|--------|------------|-------|
| Latency (cycles, in -> out)     |        |            |       |
| Fmax (MHz) / WNS (ns)           |        |            |       |
| LUT / FF / BRAM / DSP           |        |            |       |

Target board: PYNQ-Z2 (1G Ethernet only, no 10G). Packets are fed from the PS over AXI-Stream/DMA,
so there is no real NIC path. Design and measurement approach are the same as for a NIC-fed design.

## Design decisions

_Write these as you make them: why registers vs BRAM, how backpressure is handled, pipelining
before/after, fixed-latency guarantees._
