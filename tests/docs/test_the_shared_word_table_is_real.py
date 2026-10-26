"""The four arrangements in limitations.md, run.

They document a ceiling, which makes them exactly the kind of claim that
rots: somebody improves the scorer, one of these rows starts passing, and
the documentation goes on saying it cannot be done."""

from __future__ import annotations

from typing import ClassVar

from lexmatch import Entry, Index


class TestTheSharedWordTableIsReal:
    """The four arrangements in limitations.md, run.

    They document a ceiling, which makes them exactly the kind of claim that
    rots: somebody improves the scorer, one of these rows starts passing, and
    the documentation goes on saying it cannot be done.
    """

    NOTICE: ClassVar[Entry] = Entry(
        question="What is your notice period?", answer="NOTICE", aliases=["notice"]
    )
    RATE_PLAIN: ClassVar[Entry] = Entry(
        question="What are your rate expectations?",
        answer="RATE",
        aliases=["rate", "salary", "compensation"],
    )
    RATE_WITH_COST: ClassVar[Entry] = Entry(
        question="What are your rate expectations?",
        answer="RATE",
        aliases=["rate", "salary", "compensation", "what would you cost"],
    )
    MEANT_RATE = "what would you cost us"
    MEANT_COST = "how do you reduce cost"

    def _answer(self, index: Index, query: str) -> str:
        reply = index.reply(query)
        return reply.entry.answer if reply.answered else reply.outcome.value.upper()

    def test_cost_on_the_reduction_entry_gets_the_rate_question_wrong(self):
        index = Index(
            [
                self.RATE_PLAIN,
                Entry(
                    question="How do you reduce cost?",
                    answer="COST",
                    aliases=["cost", "cloud spend", "savings"],
                ),
                self.NOTICE,
            ]
        )
        assert self._answer(index, self.MEANT_RATE) == "COST"
        assert self._answer(index, self.MEANT_COST) == "COST"

    def test_adding_the_phrase_to_the_rate_entry_loses_both(self):
        """The obvious fix, which makes it worse — the row worth dwelling on."""
        index = Index(
            [
                self.RATE_WITH_COST,
                Entry(
                    question="How do you reduce cost?",
                    answer="COST",
                    aliases=["cost", "cloud spend", "savings"],
                ),
                self.NOTICE,
            ]
        )
        assert self._answer(index, self.MEANT_RATE) == "AMBIGUOUS"
        assert self._answer(index, self.MEANT_COST) == "AMBIGUOUS"

    def test_rephrasing_the_other_entry_just_moves_the_error(self):
        index = Index(
            [
                self.RATE_WITH_COST,
                Entry(
                    question="How do you keep cloud spend down?",
                    answer="COST",
                    aliases=["cloud spend", "savings", "efficiency", "spend"],
                ),
                self.NOTICE,
            ]
        )
        assert self._answer(index, self.MEANT_RATE) == "RATE"
        assert self._answer(index, self.MEANT_COST) == "RATE"

    def test_one_entry_owning_the_word_answers_both(self):
        """The arrangement the documentation recommends."""
        index = Index(
            [
                Entry(
                    question="What do you cost?",
                    answer="BOTH",
                    aliases=[
                        "rate",
                        "salary",
                        "what would you cost",
                        "reduce cost",
                        "cost reduction",
                        "cloud spend",
                    ],
                ),
                self.NOTICE,
            ]
        )
        assert self._answer(index, self.MEANT_RATE) == "BOTH"
        assert self._answer(index, self.MEANT_COST) == "BOTH"
        assert self._answer(index, "whats your rate") == "BOTH"
        assert self._answer(index, "what is your notice period") == "NOTICE"

    def test_a_phrase_alias_contributes_its_words(self):
        """The mechanism behind all of the above, asserted directly."""
        index = Index([self.RATE_WITH_COST, self.NOTICE])
        position = index.entries.index(self.RATE_WITH_COST)
        assert "cost" in index._documents[position]
