"""Words too common to carry meaning in a query.

Dropped before BM25 scoring, because a word appearing in every entry has
no discriminating power and would let any two questions look similar. They
are kept for phrase scoring, where the *arrangement* of common words is
exactly the signal — "what do you do?" is nothing but stopwords.

Adding a word is the usual tuning step. Check first that it is not
meaningful in some corpus: "about" is filler in "tell me about X" and
content in "an about page".
"""

from __future__ import annotations

STOPWORDS = frozenset(
    [
        "a",
        "about",
        "an",
        "and",
        "any",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "but",
        "by",
        "can",
        "could",
        "did",
        "do",
        "does",
        "doing",
        "for",
        "from",
        "had",
        "has",
        "have",
        "having",
        "he",
        "her",
        "him",
        "his",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "me",
        "my",
        "of",
        "on",
        "or",
        "our",
        "ours",
        "she",
        "should",
        "so",
        "some",
        "tell",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "to",
        "us",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "whom",
        "why",
        "will",
        "with",
        "would",
        "you",
        "your",
        "yours",
        # Question-form words: the verbs and hedges a question is built from,
        # which say nothing about its subject. They were missing, and in a
        # question set small enough to hand write they are *rare* — so the
        # inverse document frequency weighting treated them as the most
        # discriminating words in the index.
        #
        # Measured: "how do you think about throughput" was answered with
        # "How do you think about security?" at 0.713, because "think" scored
        # the same weight as "throughput" and the security entry shared the
        # whole form. With "think" dropped, the only content word left is
        # "throughput", which is an alias of the scale entry, and it wins at
        # 1.000.
        #
        # Words that look like this but are *not* here, because they are the
        # subject of real questions: "work" (remote work), "manage" (have you
        # managed a team), "build", "design", "process", "lead", "support",
        # "test". Adding one of those is how an index stops being able to
        # answer its own questions.
        "actually",
        "approach",
        "consider",
        "deal",
        "ever",
        "feel",
        "get",
        "got",
        "handle",
        "kindly",
        "know",
        "like",
        "long",
        "look",
        "make",
        "many",
        "maybe",
        "mean",
        "much",
        "often",
        "opinion",
        "perhaps",
        "please",
        "really",
        "say",
        "see",
        "take",
        "think",
        "use",
        "usually",
        "view",
        "want",
    ]
)
