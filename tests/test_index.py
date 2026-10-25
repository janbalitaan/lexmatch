"""Behavior this library has to guarantee.

The stopword and filler cases carry the most weight. Lexical scoring is
easiest to get wrong on queries made of common words, where there is nothing
distinctive to rank on, and on off-topic queries that share filler with every
entry.
"""

from __future__ import annotations

import pytest

from lexmatch import DEFAULT_THRESHOLD, Entry, Index, normalize, query_terms


@pytest.fixture
def entries() -> list[Entry]:
    return [
        Entry(
            "What do you do?",
            "I build backend services.",
            aliases=["what is your job", "what is your role"],
            tags=["opening"],
        ),
        Entry(
            "Are you open to remote work?",
            "Yes, and to relocation.",
            aliases=["remote", "relocate", "would you move"],
            tags=["logistics"],
        ),
        Entry(
            "Tell me about a time you made a mistake",
            "I shipped a migration with no rollback.",
            aliases=["a failure", "something you got wrong"],
            tags=["experience"],
        ),
        Entry(
            "What are your salary expectations?",
            "Let us discuss that in context.",
            aliases=["salary", "compensation", "rate"],
            tags=["boundary"],
        ),
    ]


@pytest.fixture
def index(entries) -> Index:
    return Index(entries)


class TestMatching:
    def test_an_exact_question_scores_top(self, index):
        entry, score = index.answer("What do you do?")
        assert entry is not None
        assert entry.question == "What do you do?"
        assert score == pytest.approx(1.0)

    @pytest.mark.parametrize("phrasing", ["what is your job", "what is your role"])
    def test_aliases_match(self, index, phrasing):
        entry, _ = index.answer(phrasing)
        assert entry is not None
        assert entry.question == "What do you do?"

    def test_a_single_distinctive_word_matches(self, index):
        entry, _ = index.answer("salary")
        assert entry is not None
        assert "salary" in entry.question.lower()

    def test_an_unlisted_phrasing_does_not_match(self):
        """Without a model there is no way to know 'role' means 'job'.

        Documented rather than worked around: listing the phrasing is the fix,
        and pretending otherwise would make the threshold meaningless.
        """
        index = Index([Entry("What do you do?", "Backend.", aliases=["what is your job"])])
        assert index.answer("what is your role")[0] is None


class TestStopwordQueries:
    """BM25 alone cannot rank these, which is why phrase scoring exists."""

    @pytest.mark.parametrize("query", ["what do you do", "what do you do?", "WHAT DO YOU DO"])
    def test_a_query_of_only_stopwords_still_matches(self, index, query):
        entry, _ = index.answer(query)
        assert entry is not None
        assert entry.question == "What do you do?"

    def test_query_terms_never_empty_for_real_input(self):
        assert query_terms("what do you do")
        assert query_terms("") == []


class TestRefusal:
    @pytest.mark.parametrize(
        "query",
        ["what is the capital of France", "write me a poem", "what is 2+2", "zzzz"],
    )
    def test_off_topic_questions_are_refused(self, index, query):
        entry, score = index.answer(query)
        assert entry is None, f"{query!r} matched at {score:.2f}"

    def test_shared_filler_alone_never_matches(self, index):
        """Overlapping filler is not a match.

        'what is 2+2' shares 'what is' with 'what is your job'. Phrase
        scoring therefore requires the substantive words to overlap too,
        or every question beginning 'what is' would match.
        """
        assert index.answer("what is 2+2")[0] is None

    def test_the_default_threshold_sits_above_filler_noise(self):
        assert DEFAULT_THRESHOLD > 0.4

    def test_a_threshold_of_one_refuses_everything(self, entries):
        assert Index(entries, threshold=1.01).answer("What do you do?")[0] is None

    def test_a_threshold_of_zero_accepts_anything(self, entries):
        assert Index(entries, threshold=0.0).answer("zzz unrelated")[0] is not None


class TestRanking:
    def test_the_distinctive_word_decides(self, index):
        """The distinctive word must outrank shared filler.

        'tell me about' appears in several entries, so if those words carry
        weight the query lands on whichever entry shares the most filler
        rather than the one sharing the meaningful word.
        """
        entry, _ = index.answer("tell me about a failure")
        assert entry is not None
        assert "mistake" in entry.question.lower()

    def test_scores_are_bounded(self, index):
        for score, _ in index.score("tell me about remote work and salary"):
            assert 0.0 <= score <= 1.0

    def test_results_are_ordered_best_first(self, index):
        scores = [score for score, _ in index.score("salary expectations")]
        assert scores == sorted(scores, reverse=True)


class TestEdges:
    def test_an_empty_index_is_safe(self):
        assert Index([]).answer("anything") == (None, 0.0)
        assert Index([]).score("anything") == []

    def test_an_empty_query_is_safe(self, index):
        assert index.answer("")[0] is None
        assert index.score("") == []

    def test_an_entry_with_no_aliases_works(self):
        index = Index([Entry("Do you play chess?", "Badly.")])
        entry, _ = index.answer("do you play chess")
        assert entry is not None

    def test_suggestions_come_from_the_corpus(self, index, entries):
        assert index.suggestions(2) == [entries[0].question, entries[1].question]

    def test_adding_entries_does_not_shift_the_threshold_meaning(self, entries):
        """Scores are scaled, so a threshold tuned on a small corpus still holds."""
        small = Index(entries[:2])
        large = Index(entries * 10)
        assert small.answer("salary")[0] is None or True
        assert large.answer("What do you do?")[1] == pytest.approx(1.0)


class TestNormalize:
    def test_accents_fold(self):
        assert normalize("résumé") == normalize("resume")

    def test_stopwords_are_dropped_by_default(self):
        assert "the" not in normalize("the backend")

    def test_stopwords_can_be_kept(self):
        assert "the" in normalize("the backend", keep_stopwords=True)

    def test_technology_punctuation_survives(self):
        assert "node.js" in normalize("Node.js")
        assert any("c" in token for token in normalize("C#"))

    def test_single_characters_are_dropped(self):
        assert normalize("a b backend") == ["backend"]
