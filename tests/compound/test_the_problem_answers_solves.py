"""The problem answers solves."""

from __future__ import annotations

import pytest

from lexmatch import Index
from tests.compound.a_message_asking_several_things import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestTheProblemAnswersSolves:
    def test_answer_replies_to_only_one_part(self, index):
        replies = index.answer("are you remote and what are your rates?")
        assert replies[0] is not None
        assert len(index.answers("are you remote and what are your rates?")) == 2

    def test_a_three_part_message_degrades_every_score(self, index):
        """The arithmetic, demonstrated rather than asserted.

        Each part is diluted by the others, so no part scores what it would
        have scored alone. How far it falls has moved with the scorer — the
        second part used to drop below the threshold and now clears it — so
        what is asserted is the dilution itself, not a particular depth.
        """
        whole = index.score("remote? rates? notice period?")
        alone = index.score("remote")[0][0]
        assert whole[0][0] < alone, (
            f"asking three things at once scored {whole[0][0]:.3f}, no worse "
            f"than asking one ({alone:.3f}) — the dilution is the premise"
        )
        assert whole[1][0] < whole[0][0]
        assert whole[2][0] < whole[1][0]
