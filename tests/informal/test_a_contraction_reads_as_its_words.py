"""The apostrophe is gone by the time tokens exist, so "don't" arrives
as `dont` — a token in no stopword list and in no entry, which the
weighting treats as one of the most discriminating words there is."""

from __future__ import annotations

import pytest

from lexmatch import Index
from lexmatch.contractions import Contractions
from lexmatch.text import normalize
from tests.informal.how_people_actually_type import ENTRIES


@pytest.fixture
def index() -> Index:
    return Index(ENTRIES)


class TestAContractionReadsAsItsWords:
    """The apostrophe is gone by the time tokens exist, so "don't" arrives
    as `dont` — a token in no stopword list and in no entry, which the
    weighting treats as one of the most discriminating words there is."""

    @pytest.mark.parametrize(
        ("contracted", "expanded"),
        [
            ("dont", ["do", "not"]),
            ("youve", ["you", "have"]),
            ("whats", ["what", "is"]),
            ("im", ["i", "am"]),
            ("cant", ["can", "not"]),
            ("theres", ["there", "is"]),
            ("gonna", ["going", "to"]),
        ],
    )
    def test_it_expands(self, contracted, expanded):
        assert Contractions.expand([contracted]) == expanded

    def test_the_apostrophe_form_expands_the_same_way(self):
        """One entry covers both, because normalizing strips it first."""
        assert normalize("don't", keep_stopwords=True) == ["do", "not"]

    def test_an_ordinary_word_is_untouched(self):
        assert Contractions.expand(["remote", "rate"]) == ["remote", "rate"]

    def test_the_order_is_kept(self):
        assert Contractions.expand(["whats", "your", "rate"]) == ["what", "is", "your", "rate"]

    def test_holds_reports_membership(self):
        assert Contractions.holds("dont")
        assert not Contractions.holds("remote")

    def test_an_ambiguous_form_is_left_alone(self):
        """ "ill", "well", "id", "wed" and "lets" are words. Expanding them
        is wrong as often as it is right."""
        for word in ("ill", "well", "id", "wed", "lets", "hes", "shes"):
            assert not Contractions.holds(word), word

    def test_the_table_is_replaceable(self):
        assert Contractions.FORMS["dont"] == ("do", "not")

    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("whats your notice period", "NOTICE"),
            ("im looking for a remote role", "REMOTE"),
            ("whats ur rate", "RATE"),
            ("hows your experience", "YEARS"),
        ],
    )
    def test_the_question_is_answered(self, index, message, expected):
        reply = index.reply(message)
        assert reply.answered, f"{message!r} was refused"
        assert reply.entry.answer == expected
