from itertools import combinations

import numpy as np
import pytest

from swarmtrace.review_controls import uniform_coverage


def test_exact_uniform_coverage_matches_exhaustive_subsets():
    for candidates in range(1, 9):
        for recent in range(1, candidates + 1):
            for actions in range(candidates + 1):
                subsets = list(combinations(range(candidates), actions))
                hits = np.array([sum(i < recent for i in subset) for subset in subsets])
                expected, pzero = uniform_coverage(candidates, recent, actions)
                assert expected == pytest.approx(hits.mean() / recent)
                assert pzero == pytest.approx((hits == 0).mean())


def test_exact_uniform_coverage_rejects_impossible_or_empty_recent_sets():
    for args in [(0, 0, 0), (3, 0, 1), (3, 4, 1), (3, 1, -1), (3, 1, 4)]:
        with pytest.raises(ValueError):
            uniform_coverage(*args)
