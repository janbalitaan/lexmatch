# Changelog

This project follows [semantic versioning](https://semver.org). Until 1.0.0
the public API may change in a minor release; anything that would break a
caller is listed under **Changed** with what to do about it.

## [Unreleased]

## [0.1.0] — 2026-10-26

### Added

- Two and a half times faster, from work that was being repeated rather than
  from any change to what is computed.
  - The query was normalized, typo-corrected and synonym-expanded inside
    `_phrase_score`, which runs once per entry — so all three happened once
    per entry rather than once per query. Profiled over 5,000 entries that
    was 200,000 calls for ten responses.
  - `answers()` and `unanswered()` each chose between the strict and loose
    readings separately, so one `respond()` scored every entry four times.
    The choice is made once and both use it.
  - Measured on 5,000 entries: 62 ms to 24 ms for a compound message, 12 ms
    for a single question. The scan is still linear, which is inherent; the
    constant was not.
- `Index.respond()` and `Composer`, which write the whole turn as one
  sentence. `answers()` returned a list and `unanswered()` the questions it
  missed, leaving the caller to assemble the reply — the same code in every
  application, and written badly, because the cases are not obvious until
  you have hit them: three answers run together read as a dump, a missed
  question left unmentioned reads as having been understood, and an
  ambiguous question answered at all reads as a guess.
  - Nothing is invented. Every sentence is either an entry's own answer or
    one of `Composer`'s fixed phrases, so a response can say nothing the
    owner did not write. An answer's wording is untouched except for a full
    stop when it has none, because answers run together without one read as
    a single sentence meaning something else.
  - Every phrase is a class attribute, so an application with a voice of its
    own subclasses `Composer`, overrides what it needs, and keeps the
    sequencing — the connective before the last of several, the lower-casing
    after it, the comma-and-"and" of a list.
  - A missed question is turned back into a topic: "I don't have an answer
    about *what is* your favourite film" reads as a transcript of the input
    rather than as part of a reply.
- `answers()` now replies to each question through `reply()` rather than
  `answer()`. Using the simpler one bypassed every check `reply()` exists
  for, on exactly the messages most likely to need them — an ambiguous part
  of a compound message was answered with the first of its contenders, and a
  negative part was answered affirmatively.
- A comma separates questions in the loose reading, so "whats your design
  rate, notice period, and are you remote" answers all three instead of one.
  Loose only, because "Hello, what are your rates" is one question with a
  greeting in front of it and nothing syntactic tells those apart — it wins
  only when it finds strictly more answers.
- Synonym keys may be phrases. `{"how much": "rate"}` is the point: a
  paraphrase sharing no word with the question is the one thing neither
  stopwords nor single-word synonyms can bridge. An earlier version refused
  a multi-word key on the grounds that expansion happened one token at a
  time — a statement about the implementation rather than a constraint, and
  the implementation changed. Matched longest first, so a map holding both
  "how much" and "much" reads the pair as the pair.
- The query pipeline runs in the order the features need: normalize keeping
  stopwords, correct typos, expand synonyms, *then* strip stopwords.
  Stripping first destroyed a phrase synonym made of stopwords, so
  `{"how much": "rate"}` never fired on "how much do you charge" — the exact
  paraphrase phrase keys exist for.
- A query word that appears in no entry no longer counts against the phrase
  overlap. Dice is `2|A∩B| / (|A|+|B|)`, and a word in no entry can never be
  in an intersection — so counting it lowered every score equally. With
  "how much do you charge for design" the correct entry ranked first either
  way but scored 0.400 against a 0.45 threshold: the right answer, refused.
  It scores 0.600 now.
  - The content-overlap guard still runs on the *unfiltered* query, because
    an unknown word is the evidence that the question is off-topic. Filtering
    before the guard turned "what is the capital of France" into a
    stopword-only query — the one shape allowed to match on filler — and it
    matched "What is your rate" on "what is". Eighteen tests caught it.
  - The filter is skipped entirely for a query of nothing but stopwords,
    where the filler *is* the signal: "who are you" and "what do you do"
    differ only in their filler, and dropping the unknown word shrank the
    denominator and pushed a filler-only match over the threshold.
- `Index.reply()` and the `Reply`/`Outcome` models, for the three ways a
  query fails that each need a different thing said. `answer()` returns a
  pair, which is enough to know whether anything matched and not enough to
  behave like a chatbot.
  - **Ambiguity was answered silently.** Two entries tied at 0.727 and
    `answer()` returned the first — a confident wrong answer half the time,
    with no way for the visitor to tell which half. `reply()` reports
    `AMBIGUOUS` and offers both, so a caller can ask which was meant.
    `ambiguity_margin` on the tuning decides how close counts as tied.
  - **A negative question was answered affirmatively.** "Are you *not* open
    to remote work" matched the affirmative entry at 0.923 and was answered
    "Yes" — the opposite of correct. Lexical matching cannot tell a question
    from its negation: they share every substantive word, and the negating
    words are stopwords stripped before scoring sees them. `reply()` reports
    `NEGATED` and names the closest match, so a caller can rephrase or
    escalate rather than answer wrongly. Detection, not resolution.
  - **Suggestions ignored the query.** A failed question was offered the
    first few entries in the index whatever it had asked. They are ranked by
    score now, so a near miss is offered what it nearly matched, and an
    entry scoring zero is not offered at all.
  - `reply.describe()` carries the outcome and the shape of the result and no
    question or answer text, because a log of what visitors asked is
    personal data.
- `Negation`, exported for a caller who wants the check without the reply.
- Typo correction, on by default. A lexical matcher refusing "whats your
  raets" reads as stupidity — a person answers without noticing — and
  neither aliases nor synonyms help, because a misspelling is not a word
  anybody would declare. An unrecognized token is compared against the
  index's own vocabulary, so a query can only be corrected toward something
  this index could answer. `'whats your raets'` went 0.000 to 0.723,
  `'pricng'` 0.000 to 0.978. A token already in the vocabulary is never
  touched; tokens under four characters are skipped, since below that
  almost everything is one edit from everything; and a tie is left alone.
  `Tuning().with_corrections(enabled=False)` turns it off for an index of
  product codes, where every token is one edit from another.
- `SmallTalk`, for the things people say that are not questions. A bot that
  refuses "thanks!" reads as broken in a way that refusing an obscure
  question does not. Six intents — greeting, farewell, thanks, identity,
  capability, wellbeing — with the phrasings shipped and the replies yours,
  because how somebody says hello is the same everywhere and what the bot
  says back is not. An unknown intent raises rather than leaving the handler
  silently absent.
- `Synonyms`, for a word that means the same thing across the whole index.
  Aliases attach a phrasing to one entry, so a short form used everywhere
  meant writing it into every entry — the same fact recorded five times, and
  the fifth entry is the one somebody forgets. Declared once through
  `Tuning().with_synonyms({"wfh": "work from home"})`; both the entries and
  the queries go through the same map, and the original token is kept
  alongside its expansion so a short form still matches an entry that uses
  the short form. A multi-word key raises, since expansion is token by token
  and a map that silently does nothing looks exactly like one that works.
- `Index.answers()` and `Index.unanswered()`, for a message that asks more
  than one thing. A compound message scores *worse* against every entry than
  any one part would alone, because the phrase measure is an overlap ratio:
  on "remote? rates? notice period?" the best entry reached 0.480 and the
  other two 0.400 and 0.250, both under the threshold — one answer and two
  silent omissions. Split first and each part scores as a standalone
  question. `unanswered()` names the parts that found nothing, so a reply can
  say what it missed rather than answer two of three and leave the third
  unmentioned.
- `suggestions()` leaves small talk out. Offering "hello" and "thanks" to
  somebody whose question could not be answered reads as not having
  understood that they asked a question at all.
- `answers()` weighs a strict and a loose reading of a compound message and
  takes whichever finds more answers. The strict rule splits on `and` only
  before an interrogative word, which keeps "remote and hybrid work" whole —
  correctly — and also kept "comp and notice period" whole, which answered
  one half silently. No syntactic rule separates those; the loose reading is
  tried as a second opinion and discarded unless it finds strictly more.
- `QuestionSplitter`, exported so an application can decide for itself
  whether a message is one question or several. Conservative by design:
  `and` splits only before an interrogative word, so "remote and hybrid
  work" stays one question while "what are your rates and when can you
  start" becomes two.
- `Tuning`, which makes every number the scorer uses replaceable — the
  threshold, the term-frequency saturation, the length penalty, the minimum
  content overlap and the stopword list. They were constants read straight
  out of the module, so a domain the defaults suit badly had no recourse
  short of editing the installed package. Frozen, so an index cannot have
  its scoring changed after it was built, and `Tuning()` equals the shipped
  constants exactly.
- `Tuning.with_stopwords(words, *, extra, keep)`. Three ways because three
  different things go wrong: `extra` for words that are noise in one domain,
  `keep` for a stopword that is content there — "can" is also a tin, "will"
  is also a legal document — and `words` to replace the list for another
  language. A word in both `extra` and `keep` is kept, since asking to keep
  it is the more specific instruction.
- `LexmatchError` and `TuningError`, in their own directory. A tuning value
  outside its range now raises when the tuning is built rather than
  surfacing as an index that silently never matches.
- Seven documentation pages, three runnable examples, and `SECURITY.md`.

### Fixed

- `MIN_CONTENT_OVERLAP` was exported, documented and never read: the phrase
  scorer hard-coded "any overlap at all", so a caller who raised it got no
  change and no error. It is read now — with four entries sharing most of
  their wording, a query matching one diluted word scores 0.769 at the
  default and is refused at 2.
- `__all__` listed `Tuning`, `TuningError` and `LexmatchError` without their
  imports, so the package advertised three names it did not have and
  `from lexmatch import *` would have raised. Guarded by a test now, since
  every existing test imported the names it needed directly and so nothing
  noticed.

First release.

### Added

- BM25 scoring over short question and answer pairs, with no dependencies and
  no model.
- Phrase scoring, so a query made entirely of stopwords — "what do you do?" —
  still matches. Plain BM25 cannot rank those, because the words appear in
  every entry and carry no IDF.
- A refusal threshold. Below it `answer()` returns `None`, because an
  off-topic question scores 0.2–0.4 on shared filler alone and a confident
  wrong answer is worse than no answer.
- Scores scaled to 0–1, so a threshold means the same thing whatever the
  corpus size.
- Aliases weighted as heavily as the question itself.
- No dependencies. Python 3.10 and newer, fully typed, with `py.typed`.

[Unreleased]: https://github.com/janbalitaan/lexmatch/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/janbalitaan/lexmatch/releases/tag/v0.1.0
