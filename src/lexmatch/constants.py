"""The tunable numbers, in one place.

These are what someone adjusts when matching is too eager or too reluctant.
Scattered through the modules that use them they are effectively
undiscoverable; collected here they can be read and changed as a set.

What is deliberately not here: the private regex `text.py` uses to split
words. That is implementation detail for one function, and moving it away
from that function would make both harder to read. A constant earns a place
in this file by being something a caller might want to change.
"""

from __future__ import annotations

# Below this, `answer()` returns None rather than a weak match.
#
# The number is not arbitrary: an off-topic question scores roughly 0.2 to 0.4
# on shared filler words alone, so the bar has to sit above that band. For
# question answering, refusing matters more than ranking — a confident wrong
# answer is worse for the reader than no answer at all.
DEFAULT_THRESHOLD = 0.45

# BM25 parameters, named for what they do rather than for the paper.
#
# Saturation is the paper's k1. Above it, repeating a term stops helping —
# a question mentioning "python" five times is not five times more about
# Python than one mentioning it once.
TERM_FREQUENCY_SATURATION = 1.4

# The paper's b. How much a long entry is discounted, because a long entry
# matches more queries by accident than a short one does.
LENGTH_PENALTY = 0.72

# Phrase scoring needs at least this much overlap of substantive words before
# a shared phrasing counts for anything. Without the guard, two questions
# beginning "what is" match on that alone.
MIN_CONTENT_OVERLAP = 1

# How alike a mistyped word and a real one have to be before the first is
# read as the second. Measured as difflib's ratio over the whole token, so
# 0.8 is roughly one edit in five characters.
#
# High on purpose: a wrong correction answers a question nobody asked, which
# is worse than refusing a question somebody did.
CORRECTION_SIMILARITY = 0.8

# Tokens shorter than this are never corrected. At three characters or fewer
# almost everything is within one edit of everything else, so "api" would
# "correct" to "and" and a query about an API would be answered as a
# conjunction.
CORRECTION_MINIMUM_LENGTH = 4
