"""A mistyped word corrects toward how the entry was *asked*, not its answer.

The distinction matters because the two sets are used differently. Scoring
wants the answer's words as a weak signal, so a visitor quoting a phrase from
an answer still finds it. Typo correction must not: a correction target that
appears only deep in an answer manufactures matches on words the visitor
never used and the owner never offered as a way to ask.
"""

from __future__ import annotations

from lexmatch import Entry, Index

SALARY = Entry(
    question="What are your salary expectations?",
    answer="I would rather discuss that in context. Email me.",
    aliases=("salary", "compensation"),
    tags=("boundary",),
)
WORK = Entry(
    question="What do you do?",
    answer="I build backend services and the tooling around them.",
    aliases=("your job",),
)


class TestWhatATypoMayCorrectToward:
    def test_a_word_from_an_answer_is_not_a_correction_target(self):
        """ "content" is one edit from "context", and that answer ends
        "...discuss that in context" — which was enough to make a question
        about someone's work retrieve one about their salary."""
        index = Index([SALARY, WORK])
        match, score = index.answer("tell me about the content of your work")
        assert match is None
        assert score == 0.0

    def test_the_same_word_alone_matches_nothing(self):
        index = Index([SALARY, WORK])
        assert index.answer("content")[0] is None

    def test_a_typo_in_the_question_still_corrects(self):
        """The feature this protects: correction toward a real way of asking."""
        index = Index([SALARY, WORK])
        match, _score = index.answer("what are your salry expectations")
        assert match is not None
        assert match.question == "What are your salary expectations?"

    def test_a_typo_in_an_alias_still_corrects(self):
        index = Index([SALARY, WORK])
        match, _score = index.answer("whats your jobb")
        assert match is not None
        assert match.question == "What do you do?"

    def test_a_typo_in_a_tag_still_corrects(self):
        index = Index([SALARY, WORK])
        match, _score = index.answer("boundry")
        assert match is not None

    def test_an_answers_words_still_score(self):
        """Unchanged: the answer body remains a weak signal, so a visitor
        quoting a phrase from one still finds it. Only *correcting toward*
        those words stopped."""
        index = Index([SALARY, WORK])
        match, score = index.answer("backend services")
        assert match is not None
        assert match.question == "What do you do?"
        assert score > 0.0

    def test_an_exact_answer_phrase_still_scores(self):
        index = Index([SALARY, WORK])
        match, _score = index.answer("the tooling around them")
        assert match is not None
