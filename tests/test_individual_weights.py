"""CPU tests for individual HashGrid weight indexing."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research/priority/hashgrid_ntc114"))
from map_individual_weights import (
    BLOCK, HASH_BLOCKS, make_csr, merge_weight_pairs,
    quaternion_angle, weight_accesses,
)


class IndividualWeightTests(unittest.TestCase):
    def setUp(self):
        self.layout = [(0, 0, 64, 4, np.float32(3))]
        self.mask = np.zeros(HASH_BLOCKS, dtype=np.bool_)
        self.mask[:4] = True
        self.primes = (1, 2654435761, 805459861)

    def access(self, coords, layout=None):
        return weight_accesses(
            np.asarray(coords, np.float32),
            self.layout if layout is None else layout,
            4, "linear", self.primes, self.mask)

    def test_one_vertex_has_four_exact_feature_ids(self):
        g, w, c = self.access([[0.5, 0.5, 0.5]])
        np.testing.assert_array_equal(g, [0, 0, 0, 0])
        np.testing.assert_array_equal(w, [168, 169, 170, 171])
        np.testing.assert_allclose(c, [1, 1, 1, 1])

    def test_trilinear_coefficients_sum_to_one_per_feature(self):
        g, w, c = self.access([[0.25, 0.25, 0.25]])
        self.assertEqual(len(w), 32)
        for channel in range(4):
            self.assertAlmostEqual(float(c[w % 4 == channel].sum()), 1, places=6)

    def test_hash_collisions_merge_coefficients(self):
        hashed_layout = [(0, 0, 8, 16, np.float32(15))]
        g, w, c = self.access([[0.123, 0.246, 0.369]], hashed_layout)
        keys, merged = merge_weight_pairs(g, w, c, 1)
        self.assertLessEqual(len(keys), 8 * 4)
        for channel in range(4):
            self.assertAlmostEqual(
                float(merged[keys % 4 == channel].sum()), 1, places=5)

    def test_sparse_lookup_reverses_weight_and_gaussian(self):
        coords = np.asarray([[0.25, 0.25, 0.25],
                             [0.5, 0.5, 0.5],
                             [0.99, 0.1, 0.1]], np.float32)
        good = np.asarray([True, True, False])
        retained = np.arange(4, dtype=np.int32)
        w, offsets, gids, c = make_csr(
            coords, good, self.layout, 4, "linear",
            self.primes, retained, batch=2)
        self.assertEqual(len(w), 4 * BLOCK)
        self.assertEqual(len(offsets), len(w) + 1)
        self.assertEqual(int(offsets[-1]), len(gids))
        self.assertTrue(np.all(gids < 2))
        row = int(np.flatnonzero(w == 168)[0])
        np.testing.assert_array_equal(gids[offsets[row]:offsets[row + 1]], [0, 1])
        self.assertAlmostEqual(float(c[offsets[row]]), 0.015625, places=6)

    def test_unretained_blocks_produce_no_pairs(self):
        self.mask[:] = False
        g, w, c = self.access([[0.25, 0.25, 0.25]])
        self.assertEqual(len(g), 0)
        self.assertEqual(len(w), 0)
        self.assertEqual(len(c), 0)

    def test_quaternion_difference_handles_identity_and_sign(self):
        q = np.asarray([[1, 0, 0, 0], [0, 0, 0, 0]], np.float32)
        other = np.asarray([[0, 1, 0, 0], [0, 0, 0, 0]], np.float32)
        np.testing.assert_allclose(quaternion_angle(q, other), [180, 0], atol=0.0001)
        np.testing.assert_allclose(quaternion_angle(q, -q), [0, 0], atol=0.0001)


if __name__ == "__main__":
    unittest.main()
