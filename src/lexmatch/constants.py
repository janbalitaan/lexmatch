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

# How close the runner-up has to be before a question counts as ambiguous
# rather than answered. Measured as a difference in score.
#
# Both entries cleared the threshold, so the question was understood — it
# just was not specific enough to choose between them. Guessing is a
# confident wrong answer half the time, and the visitor cannot tell which
# half they got.
AMBIGUITY_MARGIN = 0.05

# The score a contender has to reach before a tie counts as ambiguity rather
# than as two weak guesses.
#
# A tie is only worth asking about when both candidates are confidently
# matched. Below the floor the tie is reported as unanswered with the
# contenders as suggestions, which is honest: several candidates at a middling
# score mean the question was not understood, and letting the asker choose
# beats a one-in-four guess.
#
# This started at 0.65, chosen when "what do you work on" tied four ways at
# 0.537 and asked "remote work, or visa sponsorship?" — which read as
# nonsense. That tie was an artifact of weighting every shared token equally:
# the four entries shared "work" plus filler and nothing else. Once phrase
# overlap was weighted by inverse document frequency the same query scored
# 0.921 against one entry and 0.000 against the rest, so the floor was no
# longer holding back anything it was built for — and at 0.65 it had started
# refusing *genuine* ambiguity instead, which measures 0.580 for two rate
# entries and 0.633 for two notice-period entries.
#
# 0.50 sits below both and above the noise. The knob stays because an index
# whose entries are near-duplicates may want it higher.
AMBIGUITY_FLOOR = 0.50

# How many alternatives to offer for a genuine ambiguity. Two is a question;
# five is a menu, and a menu is what `suggestions` is for.
AMBIGUITY_ALTERNATIVES = 3


# The tag `SmallTalk.entries` puts on what it builds, and the marker `Index`
# reads to know an entry is a social formula rather than a subject.
#
# Social phrasings are short, and the length penalty favours short entries, so
# a message that merely *contains* a pleasantry used to be answered by one.
# Measured over fifteen simulated visitors: "is the pay good" scored 1.000
# against the greeting entry, on "good" matching "good morning"; "do you care
# about the frontend at all" scored 0.957 against the farewell, on "care"
# matching "take care". Both are real questions with a social word in them.
#
# Renaming this is enough to opt a custom set of entries into the same
# treatment, or out of it.
SMALL_TALK_TAG = "smalltalk"


# How much a word the index has never seen costs the query's confidence.
#
# An unknown word has no inverse document frequency, so it contributes
# nothing to the score ceiling and is effectively invisible — which leaves a
# query satisfiable by matching only the words it happened to share. Measured
# against a twenty-five entry index, "what dashboards do you build" scored
# 1.000 against "How do you decide build versus buy?" with "dashboards"
# discarded before anything was scored.
#
# Charging for it is nonetheless **off by default**, because measuring it
# across 133 questions from thirty-seven simulated askers showed it costs
# more than it saves: at 1.0 the suite fell from 81.2% to 73.7%, because a
# real question with one unrecognized word has its confidence halved and
# drops below the threshold. It converts correct answers into refusals faster
# than it converts wrong answers into refusals.
#
# Raise it toward 1.0 for an index where a wrong answer is worse than no
# answer — a support bot whose topics are deliberately narrow, where most of
# what it is asked is out of scope and the refusal is the product.
UNKNOWN_WORD_COST = 0.0
