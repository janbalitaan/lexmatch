"""An entry exposes two term sets, for two different jobs."""

from __future__ import annotations

from lexmatch import Entry

ENTRY = Entry(
    question="What are your salary expectations?",
    answer="I would rather discuss that in context.",
    aliases=("compensation",),
    tags=("boundary",),
)


class TestWhichTermsAnEntryOffers:
    def test_asked_terms_hold_the_question(self):
        assert "salary" in ENTRY.asked_terms()

    def test_asked_terms_hold_the_aliases(self):
        assert "compensation" in ENTRY.asked_terms()

    def test_asked_terms_hold_the_tags(self):
        assert "boundary" in ENTRY.asked_terms()

    def test_asked_terms_exclude_the_answer(self):
        """The whole point of the split."""
        assert "context" not in ENTRY.asked_terms()

    def test_terms_include_the_answer(self):
        assert "context" in ENTRY.terms()

    def test_terms_include_everything_asked_terms_does(self):
        assert set(ENTRY.asked_terms()) <= set(ENTRY.terms())

    def test_the_question_outweighs_the_answer(self):
        """Repeated, so matching on how a visitor asked outranks a word
        buried in a long answer."""
        assert ENTRY.asked_terms().count("salary") > 1
