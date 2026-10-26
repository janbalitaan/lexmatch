"""Every inflection reaches one stem."""

from __future__ import annotations

import pytest

from lexmatch.stemming import Stemmer


class TestEveryInflectionReachesOneStem:
    @pytest.mark.parametrize(
        "forms",
        [
            ("consult", "consults", "consulting", "consulted"),
            ("scale", "scales", "scaling", "scaled"),
            ("manage", "manages", "managing", "managed"),
            ("experience", "experiences", "experienced"),
            ("design", "designs", "designing", "designed"),
            ("mentor", "mentors", "mentoring", "mentored"),
            ("pair", "pairs", "pairing", "paired"),
            ("measure", "measures", "measuring", "measured"),
            ("deploy", "deploys", "deploying", "deployed"),
            ("rate", "rates"),
            ("policy", "policies"),
            ("remote", "remotely"),
        ],
    )
    def test_they_agree(self, forms):
        stems = {Stemmer.stem(form) for form in forms}
        assert len(stems) == 1, f"{forms} split into {sorted(stems)}"
