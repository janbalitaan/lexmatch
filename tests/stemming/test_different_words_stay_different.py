"""The reason this is not a Porter stemmer.

Porter strips derivational endings too, which merges words that mean
different things — "university" and "universe" both become "univers"."""

from __future__ import annotations

import pytest

from lexmatch.stemming import Stemmer


class TestDifferentWordsStayDifferent:
    """The reason this is not a Porter stemmer.

    Porter strips derivational endings too, which merges words that mean
    different things — "university" and "universe" both become "univers".
    """

    @pytest.mark.parametrize(
        ("left", "right"),
        [
            ("university", "universe"),
            ("business", "busy"),
            ("process", "profess"),
            ("training", "train"),
            ("meeting", "meet"),
            ("note", "not"),
            ("rate", "rat"),
            ("code", "cod"),
            ("payment", "pay"),
            ("consultant", "consult"),
        ],
    )
    def test_they_do_not_collide(self, left, right):
        assert Stemmer.stem(left) != Stemmer.stem(right)
