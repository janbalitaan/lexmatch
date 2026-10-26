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

from lexmatch.composer import Composer
from lexmatch.constants import (
    DEFAULT_THRESHOLD,
    LENGTH_PENALTY,
    MIN_CONTENT_OVERLAP,
    TERM_FREQUENCY_SATURATION,
)
from lexmatch.exceptions import (
    LexmatchError,
    SmallTalkError,
    SynonymError,
    TuningError,
)
from lexmatch.index import Index
from lexmatch.models import (
    Corrections,
    Entry,
    Outcome,
    Reply,
    Synonyms,
    Tuning,
)
from lexmatch.negation import Negation
from lexmatch.questions import QuestionSplitter
from lexmatch.smalltalk import SmallTalk
from lexmatch.stopwords import STOPWORDS
from lexmatch.text import normalize, query_terms

__all__ = [
    "DEFAULT_THRESHOLD",
    "LENGTH_PENALTY",
    "MIN_CONTENT_OVERLAP",
    "STOPWORDS",
    "TERM_FREQUENCY_SATURATION",
    "Composer",
    "Corrections",
    "Entry",
    "Index",
    "LexmatchError",
    "Negation",
    "Outcome",
    "QuestionSplitter",
    "Reply",
    "SmallTalk",
    "SmallTalkError",
    "SynonymError",
    "Synonyms",
    "Tuning",
    "TuningError",
    "__version__",
    "normalize",
    "query_terms",
]
__version__ = "0.1.0"
