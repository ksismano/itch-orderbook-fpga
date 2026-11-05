import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model"))

import gen_vectors  # noqa: E402
import itch  # noqa: E402


class TestCodec(unittest.TestCase):
    def test_lengths(self):
        self.assertEqual(len(itch.encode_add(1, 1, "B", 10, "AAPL", 100)), 36)
        self.assertEqual(len(itch.encode_exec(1, 1, 5, 9)), 31)
        self.assertEqual(len(itch.encode_cancel(1, 1, 5)), 23)
        self.assertEqual(len(itch.encode_delete(1, 1)), 19)
        self.assertEqual(len(itch.encode_replace(1, 1, 2, 5, 100)), 35)

    def test_roundtrip_add(self):
        (m,) = list(itch.parse_stream(itch.encode_add(42, 7, "S", 100, "MSFT", 12345)))
        self.assertEqual((m.kind, m.ts, m.ref, m.side, m.shares, m.stock, m.price),
                         ("A", 42, 7, "S", 100, "MSFT", 12345))


class TestBook(unittest.TestCase):
    def test_best_prices(self):
        s = b"".join([
            itch.encode_add(1, 1, "B", 100, "AAPL", 100),
            itch.encode_add(2, 2, "B", 50, "AAPL", 101),
            itch.encode_add(3, 3, "S", 70, "AAPL", 103),
        ])
        rows = itch.run(s)
        self.assertEqual(rows[-1][1:], ("AAPL", 101, 50, 103, 70))

    def test_exec_cancel_delete_replace(self):
        s = b"".join([
            itch.encode_add(1, 1, "B", 100, "AAPL", 100),
            itch.encode_exec(2, 1, 40, 1),      # 60 left
            itch.encode_cancel(3, 1, 10),       # 50 left
            itch.encode_replace(4, 1, 2, 30, 102),
            itch.encode_delete(5, 2),
        ])
        rows = itch.run(s)
        self.assertEqual(rows[1][2:4], (100, 60))
        self.assertEqual(rows[2][2:4], (100, 50))
        self.assertEqual(rows[3][2:4], (102, 30))
        self.assertEqual(rows[4][2:4], (0, 0))

    def test_random_stream_runs(self):
        data = gen_vectors.generate(3000, seed=3)
        rows = itch.run(data)
        self.assertGreater(len(rows), 0)


if __name__ == "__main__":
    unittest.main()
