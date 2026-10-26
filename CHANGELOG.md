# Changelog

This project follows [semantic versioning](https://semver.org). Until 1.0.0
the public API may change in a minor release; anything that would break a
caller is listed under **Changed** with what to do about it.

## [Unreleased]

## [0.1.0] — 2026-10-26

### Added

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
