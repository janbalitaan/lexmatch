# Changelog

This project follows [semantic versioning](https://semver.org). Until 1.0.0
the public API may change in a minor release; anything that would break a
caller is listed under **Changed** with what to do about it.

## [Unreleased]

## [0.1.1] — 2026-10-26

### Changed

- Five placeholder pronouns are stopwords: "other", "others", "another",
  "same", "such". They stand in for something already mentioned, and with no
  conversation state to resolve them against, a refusal is honest where a
  match on a word that happens to appear somewhere is not — "what about the
  other one" was answering a question nobody asked.

  "one" and "ones" are deliberately **not** included, though "and that one?"
  is the clearest case of the problem: "one to ones" is a whole entry's alias
  and "One month." is an answer, and dropping the word cost a question a real
  manager asked while saving one only a follow-up would. `limitations.md` has
  the rest, which needs state rather than a word list.


## [0.1.0] — 2026-10-26

### Added

- **A question asked in an entry's own words is recognized as one.** A query
  contained in one of an entry's phrasings is scored on its coverage of that
  phrasing, which the weighted comparison cannot see when the shared words
  are stopwords: "what are you working on" shares five of the seven tokens in
  "What are you working on right now?", all but one of them a stopword, so by
  content alone it matched one word that four other entries held too. A
  question that was practically quoted scored 0.489 and was refused; it
  scores 0.833 now.

  Two conditions keep it off coincidence, and each was a measured regression
  first. Coverage below 0.70 contributes nothing, because "you work" sits
  inside three of five entries and lifting it put a tie over the ambiguity
  floor. And it is only tried for a query with a substantive word, because a
  filler query is inside a great many questions at high coverage — "what do
  you do" went from answered to a refused tie across the whole index.

  It runs as a pass of its own, entered once per query. Folding it into the
  per-phrase loop as a method call cost 4 ms a reply against 5000 entries,
  which is the only reason the shape is what it is.
- Every parser takes `strict`, defaulting to true. A file loaded once at
  startup should say what is wrong with it; a file being edited while it is
  served should keep answering while its owner is halfway through the next
  question. The second case came out of integrating the library into a
  consumer that had been skipping unreadable entries for exactly that reason.
- `MarkdownParser` accepts the blockquote convention as well as the italic
  one, and a named `Tags:` line as well as `#hashtags`. Both are how people
  write a note to the reader, and accepting only one makes the other a
  configuration format.
- **A question set can be a file.** `CsvParser`, `JsonParser` and
  `MarkdownParser` read entries from the formats question sets actually live
  in — a spreadsheet export, an API response, the FAQ page that is already
  written. Until now the only way to build an index was to write Python,
  which made whoever writes the answers depend on whoever writes the code,
  for every change.

  Each raises `ParseError` naming the line, row or key at fault, because a
  question set is long and often generated. CSV counts lines the way a
  spreadsheet does, header included, so the number matches the screen. All
  three ignore columns and keys that belong to other systems, and their field
  names and separators are class attributes, so a file named differently
  loads without being rewritten.
- **An entry with no question or no answer is refused when it is built.** It
  used to be accepted and then score zero against everything, which is
  indistinguishable from an entry about something nobody asks — one is a
  broken question set and the other is normal, and nothing downstream could
  tell them apart. A blank alias is still dropped rather than refused,
  because a trailing empty column is what an export looks like.
- A token now needs a letter or a digit in it. The word pattern admits dots,
  plus signs and hashes so "node.js", "c++" and "c#" survive whole, which
  also made a run of them a token: "..." and "+++" were indexed as words.
- `Tokenizer.SHORTEST_WORD` replaces a hard-coded two. The cost of two is
  that "C" and "R" cannot be indexed; lowering it to one was measured and
  cost a question while gaining nothing the benchmarks could see, so it stays
  at two and is now a setting rather than a limitation.
- `Stemmer`, `Morphology` and `Contractions` are exported from the package
  root, which is where the documentation already said to find them, and
  `api.md` covers them.
- **Typo correction no longer merges two related words.** "designers" and
  "design" score exactly 0.800 and the length filter admitted them, so "how
  do you work with designers" was answered "How do you design a system?" at
  0.821. Somebody typing "designers" meant designers, and merging the two is
  the merge stemming refuses for the same reason.

  The line is a prefix relationship with more than one character between
  them: "designers" is "design" plus "ers", while "notic" for "notice" is a
  dropped letter. What correction now declines is `Morphology`'s work, and
  that mechanism takes it on with a stricter rule — it only lengthens toward
  a word the index holds, and it refuses an ambiguous prefix.
- Nine more question-form stopwords, the verbs of asking how something is
  decided or described: "decide", "choose", "determine", "define",
  "describe", "explain", "select", "ensure". "how do you decide when to
  refactor" matched the technical-debt entry on "refactor" at 0.482 and the
  build-versus-buy entry on "decide" at 0.452 — close enough to tie, so a
  question whose subject was clear got refused. The subject is what follows
  the verb.
- Typo correction skips the real comparison when a shared-character bound
  says no candidate can clear the threshold. Constructing a `SequenceMatcher`
  indexes its second sequence eagerly, and against 5000 entries that meant
  279,310 index builds for fifty query words — an unrecognized query cost
  92.9 ms and now costs 48.2 ms.

  The bound is what `quick_ratio` computes and a true upper bound on `ratio`,
  so the skip cannot lose a match. Indexing the token once instead, by
  swapping the arguments, is *not* available: `ratio` is asymmetric in about
  a tenth of pairs, which was measured rather than assumed. A test compares
  the gated path against an ungated reference over the vocabulary, every
  single-edit typo of it and two thousand random strings, at four
  thresholds.
- `Morphology` bridges a query word to a longer index word built from it:
  "senior" to "seniority", "secur" to "security". Stemming folds inflection
  and deliberately stops at derivation, because the endings it would have to
  stripchange what a word means — but an index that holds only the derived
  form is then unreachable, and nothing reports the failure. Typo correction
  does not bridge it either, and for a good reason: it compares only words of
  a similar length, and "senior" and "seniority" differ by three.

  A prefix rather than a similarity score, because that is what derivation
  looks like in English, and ambiguity is refused — two index words starting
  the same way means picking one is wrong half the time. Worth one question in
  133 measured, which is small and honestly stated: how often an index holds a
  derived form without its root is a property of the question set. The prefix
  length was swept and three through six scored identically, so five is a
  judgement and the comment says so. `Tuning.with_morphology(None)` turns it
  off.
- **Informal writing is read properly.** Three defects, and together they
  cost more accuracy than anything else measured: across twenty informally
  written questions, **65% answered before and 95% after**, with every other
  benchmark unchanged.
  - An **apostrophe split the word**, because the word pattern does not
    include one: "don't" became `don` with the "t" dropped as too short,
    "you've" became `you` and `ve`. The form people actually type was handled
    worse than the stripped form. Apostrophes are removed before splitting
    now, curly ones included, since those arrive from anything that
    autocorrects.
  - A **contraction read as an unknown word**, which is the rarest kind of
    word there is, so the weighting treated it as one of the most
    discriminating terms in the query — `youv` scored 3.06 against a
    twenty-five entry index, the same as the rarest real term. Each is
    replaced by the words it stands for, which are ordinary stopwords.
    `Contractions.FORMS` is replaceable, and ambiguous forms are deliberately
    absent because "ill", "well", "id", "wed" and "lets" are words.
  - A **tag question was read as a negative**. English tag questions confirm
    the clause before them — "you've led teams before, haven't you?" expects
    yes — and five of twenty questions matched **perfectly, at 1.000, and
    were thrown away**. A negated auxiliary followed by a pronoun at the end
    of a message is affirmative now, and so is a polite request at the start
    ("can't you start sooner?" asks for the notice period). A genuine
    negative is untouched.
- Nineteen placeholder nouns are stopwords: "thing", "stuff", "something",
  "way", "kind", "sort". "thing" scored 3.06 against a twenty-five entry
  index — as discriminating as the rarest real term there — so "whats the
  biggest thing youve built" spent a third of its weight on a word that says
  nothing. Not included: "time", "place", "point", "level", "number", "case",
  "part", "area" — those are the subject of real questions.
- `SmallTalk.PHRASINGS` gained the short forms people type: `thx`, `ty`,
  `tnx`, `sup`, `are you a robot`, `bot or human`, `who made you`.
- `reply()` reads a multi-part message as parts when that says something the
  whole string did not — either two distinct answers, or a part that answers
  where the whole string refused. "I don't need visa sponsorship, what's the
  stack?" was reported NEGATED, because the first clause's "not" was read
  against the second clause's answer. A pleasantry does not count as a
  rescue: answering "Good afternoon. What is the largest system you have
  designed?" with "Hello" at 1.000 is worse than refusing. Overriding a
  whole-string reply that *did* answer was measured and rejected — it cost
  4.9 points across fifteen simulated visitors.
- **Inflections fold onto one token.** "consulting" and "consult" were
  different words, and so were "built" and "build", "rates" and "rate". The
  documentation said an alias was cheaper and exact, which holds for twenty
  entries and stops holding at the scale a support index runs at — nobody
  hand-writes aliases for every tense across four hundred entries, and the
  ones they forget are the ones that fail. Measured across 133 questions from
  thirty-seven simulated askers: **76.7% to 85.0%**, with confidently wrong
  answers falling from fourteen to three.

  Only inflection folds. This is not a Porter stemmer: Porter strips
  derivational suffixes too, which merges "university" and "universe" into one
  token. `Tuning.with_stemmer(None)` turns it off and any callable replaces
  it, and `Stemmer.IRREGULAR`, `KEEP` and `SUFFIXES` are all replaceable.
- **Content decides a content question.** Phrase overlap counted shared
  stopwords, which carry real weight in a small index — "how" and "do" score
  0.66 and 0.60 against twenty-five entries — so a shared question *form*
  outranked a shared subject. "how do standups work for you" scored 0.669
  against "How do you estimate work?" on {how, do, you, work}, beating the
  agile entry's 0.637 on "standup", which is that entry's own alias and
  carries twice the weight. Stopwords now count only for a query that has
  nothing else, which is the case they were kept for.
- **A message asking two things is no longer called ambiguous.** Ambiguity is
  one question matching two entries; "yoe and tech stack?" is two questions
  matching one each, and asking which was meant answers neither. `reply()`
  scored the whole string and never consulted the split, so it disagreed with
  `answers()` about the same message. A greeting in front of a question no
  longer becomes the answer, either: the substantive part leads.
- **Thirty-two question-form stopwords.** "think", "handle", "approach",
  "consider" and the rest of the verbs and hedges a question is built from.
  They were absent, and in a question set small enough to hand write they are
  *rare*, so the weighting treated them as the most discriminating words in
  the index. Words that look like this but are deliberately not included:
  "work", "manage", "build", "design", "process" — those are the subject of
  real questions.
- `Tuning.unknown_word_cost`, **off by default**. An unknown word has no
  weight, so it is invisible, and a query is satisfiable by matching only the
  words it shares. Two ways of charging for it were implemented and measured;
  both made the library worse (82.7% and 69.9% against 85.0%), because in a
  small question set most words in a natural question are absent from every
  entry, so charging for an unknown word charges for natural phrasing. Kept
  for a deliberately narrow index where a refusal beats a guess.
- A reply against 5000 entries costs 17.8 ms on the default path, unchanged by
  any of the above. Three things were moved to build time to keep it there:
  the stemmer is memoized, each phrase's content and weight are computed once,
  and the compound reading is skipped unless the splitter says the message
  could be compound — that last one alone had doubled the cost, because
  reading a single question scored every entry two or three times.
- Two more scoring defects, found by simulating eleven professional roles —
  technical and non-technical recruiters, developers, senior developers,
  architects, product owners, scrum masters, engineering managers, a CEO, a
  CTO — and fifteen people who are not hiring anyone: a nurse, a student, a
  business owner, a journalist, a teenager, a non-native speaker, someone
  typing on a phone.
  - **A shared question *form* was read as a shared subject.** Phrase overlap
    counted every token equally, so "how do you" weighed the same as
    "refactor" — and most questions in an index share a form. "how do you
    mentor juniors" scored **1.000** against the small-talk entry "how are
    you", on two shared tokens that mean nothing. Overlap is now weighted by
    inverse document frequency, which is the same ratio over the information
    each token carries rather than over the count.
  - **Small talk answered real questions.** Social phrasings are short and
    the length penalty favours short entries, so an entry built from "take
    care" won any message containing "care": "do you care about the frontend
    at all" scored 0.957 against the farewell, and "is the pay good" scored
    1.000 against the greeting because "good" matches "good morning". A
    small-talk entry may now only answer when every substantive word in the
    message is one its own phrasings use. The marker is `SMALL_TALK_TAG`, so
    a custom set of entries can opt in or out.
  - Also found: the exact-match shortcut ran *before* the overlap guard and
    compared what survived filtering rather than what was asked, so "how do
    you mentor juniors" matched the alias "how do you do" exactly once
    "mentor" and "juniors" were dropped as unknown words. And a bare
    acknowledgement is no longer a question — "great, thanks!" was answered
    correctly while "great" was reported as unanswered, which made a right
    answer look like a partial failure.
- Each phrase's token set and weight are built with the index, and the
  query's weight once per query. Deriving them inside the ranking loop meant
  splitting every phrase of every entry and summing its weight again on every
  reply — 2.95 million `sum` calls per hundred replies against 5000 entries.
  A reply on the default path costs 18.0 ms against 5000 entries, down from
  24.7 ms, and the weighting itself costs 1.2 ms of that.
- `ambiguity_floor` lowered from 0.65 to 0.50. It was set when a four-way tie
  at 0.537 produced a nonsense clarifying question; weighting the overlap
  removed that tie — the same query now scores 0.921 against one entry and
  0.000 against the rest — so at 0.65 the floor had stopped holding back
  anything it was built for and had started refusing genuine ambiguity, which
  measures 0.580 for two rate entries.
- Three scoring defects found by simulating twenty recruiters and ten
  ordinary visitors against a realistic index — sixty-seven messages written
  the way each kind of person actually writes.
  - **A naturally phrased question scored worse than its keywords.** The
    BM25 ceiling was `max_idf * number_of_terms`, which assumes every query
    term is as rare as the rarest term in the index — so a common word was
    counted at a weight it could never earn and the ceiling grew with each
    word added. Measured: `advisory` 1.000, `advisory work` 0.512, `do you
    take on advisory work` 0.341. The same keyword, scoring worse the more
    naturally it was asked, which is backwards because people write
    sentences. Each term now contributes its own ceiling.
  - **A weak tie was reported as ambiguity.** "what do you work on" tied at
    0.537 against "Are you open to remote work" and "Do you need visa
    sponsorship" — on the word "work" plus filler — and the clarifying
    question read as nonsense. Genuine ambiguity sat at 0.727.
    `ambiguity_floor` is the score a tie has to reach before it is worth
    asking about; below it the contenders are offered as suggestions, which
    lets the visitor choose rather than taking a one-in-four guess.
  - **A query's confidence ignored how specific it was.** BM25 is normalized
    against what a query *could* achieve, which says nothing about whether
    the query was worth asking: one common content word matches 100% of what
    was askable and carries almost no information. Scaled by the query's own
    IDF mass now, so an answer can only be as confident as the question was
    specific.
  - **BM25 was ranking stopword-only queries.** `_phrase_score` documents
    that it cannot — "stopwords appear in every entry and carry no IDF" —
    but the query preparation fell back to the unstripped tokens whenever
    stripping left nothing, and fed them to BM25 anyway. Harmless while the
    ceiling was unreachable; once it was reachable, "who are you" scored
    0.921 against "Are you open to remote work" because filler was all there
    was to reach.
  - Also from the simulation: `!`, `.` and an em dash now separate questions,
    so "Hi! Quick one — YOE and CTC?" is three parts rather than one quoted
    back whole; and a one-character fragment is dropped, so "e.g." does not
    become two questions nobody asked.
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
