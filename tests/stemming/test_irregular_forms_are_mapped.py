"""No suffix rule reaches these, so they are listed."""

from __future__ import annotations

import pytest

from lexmatch.stemming import Stemmer


class TestIrregularFormsAreMapped:
    """No suffix rule reaches these, so they are listed."""

    @pytest.mark.parametrize(
        ("inflected", "base"),
        [
            ("built", "build"),
            ("bought", "buy"),
            ("led", "lead"),
            ("made", "make"),
            ("paid", "pay"),
            ("written", "write"),
            ("found", "find"),
            ("people", "person"),
            ("children", "child"),
            ("analyses", "analysis"),
        ],
    )
    def test_the_base_is_reached(self, inflected, base):
        assert Stemmer.stem(inflected) == Stemmer.stem(base)

    def test_the_mapping_is_replaceable(self):
        """Stated in the class docstring, so it is tested."""
        assert Stemmer.IRREGULAR["built"] == "build"
        assert isinstance(Stemmer.IRREGULAR, dict)
