"""BM25 question matching with phrase scoring, and no dependencies.

Built for the case where a vector database is more machinery than the problem
deserves: a few dozen to a few thousand short question/answer pairs, where the
answers are written by hand and the matching has to be predictable.

    from lexmatch import Entry, Index

    index = Index([
        Entry("What do you do?", "I build backend services.",
              aliases=["what is your job", "what is your role"]),
        Entry("Are you open to remote work?", "Yes, and to relocation."),
    ])

    entry, score = index.answer("what is your role")
    # -> the first entry, 1.0

Two things it does that plain BM25 does not:

**Phrase scoring.** BM25 cannot rank a query made entirely of stopwords —
"what do you do?" — because those words appear in every entry and carry no
IDF. Phrasing is scored separately so such questions still match.

**A refusal threshold.** Below it, `answer()` returns None. For a question
answering system this matters more than ranking: a confident wrong answer is
worse than no answer, and an off-topic question scores 0.2-0.4 on shared
filler words alone.

Scores are scaled to 0..1, so a threshold means the same thing whatever the
corpus size.
"""

from lexmatch.index import (
    DEFAULT_THRESHOLD,
    LENGTH_PENALTY,
    TERM_FREQUENCY_SATURATION,
    Entry,
    Index,
)
from lexmatch.text import STOPWORDS, normalize, query_terms

__all__ = [
    "DEFAULT_THRESHOLD",
    "LENGTH_PENALTY",
    "STOPWORDS",
    "TERM_FREQUENCY_SATURATION",
    "Entry",
    "Index",
    "__version__",
    "normalize",
    "query_terms",
]
__version__ = "0.1.0"
