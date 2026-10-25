# Changelog

This project follows [semantic versioning](https://semver.org). Until 1.0.0
the public API may change in a minor release; anything that would break a
caller is listed under **Changed** with what to do about it.

## [Unreleased]

## [0.1.0] — 2026-10-26

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
