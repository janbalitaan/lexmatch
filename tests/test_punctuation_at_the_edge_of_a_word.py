"""A period inside a word belongs to it; one at the end does not.

The token pattern has to admit periods, because "node.js", ".net" and "3.11"
are words people type. That admitted sentence punctuation too, so the last
word of every sentence became a term of its own — "context." was a token no
query could match, which quietly made the final word of each sentence in an
answer unsearchable.
"""

from __future__ import annotations

from lexmatch import Entry, Index, normalize


def tokens(text: str) -> list[str]:
    return normalize(text, keep_stopwords=True)


class TestPunctuationAtTheEdgeOfAWord:
    def test_a_trailing_period_is_not_part_of_the_word(self):
        assert tokens("in context.") == ["in", "context"]

    def test_a_sentence_final_word_matches_the_same_word_elsewhere(self):
        assert tokens("hello world.") == tokens("hello world")

    def test_a_version_number_keeps_its_period(self):
        assert "3.11" in tokens("python 3.11")

    def test_a_dotted_name_keeps_its_period(self):
        assert "node.js" in tokens("I use node.js")

    def test_a_dotted_name_at_the_end_of_a_sentence_survives(self):
        """Both at once, which is how it appears in a real answer."""
        assert "node.js" in tokens("Mostly node.js.")

    def test_a_plus_or_hash_is_kept(self):
        """ "c++" and "c#" are the words, not "c"."""
        assert "c++" in tokens("I write c++")
        assert "c#" in tokens("I write c#")

    def test_a_leading_period_is_trimmed_consistently(self):
        """Both sides of a comparison go through this, so ".net" and "net"
        meet as the same token rather than missing each other."""
        assert tokens(".net") == tokens("net")

    def test_punctuation_alone_yields_nothing(self):
        assert tokens("...") == []
        assert tokens(". , !") == []


class TestASentenceFinalWordIsSearchable:
    def test_the_last_word_of_an_answer_can_be_found(self):
        index = Index(
            [
                Entry(
                    question="What do you do?",
                    answer="I build backend services and the surrounding tooling.",
                )
            ]
        )
        match, score = index.answer("tooling")
        assert match is not None
        assert score > 0.0

    def test_the_last_word_of_a_question_can_be_found(self):
        index = Index([Entry(question="Do you know Kubernetes.", answer="Yes.")])
        match, _score = index.answer("kubernetes")
        assert match is not None
