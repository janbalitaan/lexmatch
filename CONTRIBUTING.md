# Contributing to lexmatch

The library is small on purpose: BM25 scoring, phrase scoring, and a refusal
threshold. Most useful contributions are about accuracy on real corpora
rather than new features.

## Running the checks

```bash
git clone https://github.com/janbalitaan/lexmatch
cd lexmatch
uv sync
uv run pytest
uv run ruff check src tests
uv run ty check src
uv run python scripts/complexity.py src
```

All four must pass. No function may exceed cognitive complexity 15, which the
last command enforces.

## A matching bug is worth more than a feature

If a query matches the wrong entry, or refuses one it should have matched,
that is the highest-value thing to report. Include the entries and the query,
because the fix is almost always a scoring change and a scoring change needs
a test that pins the behavior in both directions:

```python
def test_it_matches_the_right_entry(self, index):
    entry, _ = index.answer("the query that went wrong")
    assert entry.question == "the one it should have found"


def test_it_still_refuses_this(self, index):
    assert index.answer("something off topic")[0] is None
```

The second test is the one that matters. Lexical scoring is easy to improve
for one query and break for another, because every change to how tokens are
weighted moves every score.

## Why the scoring is the way it is

Three decisions are worth knowing before changing them, because each was the
fix for a specific failure:

**Stopwords are dropped from BM25 but kept for phrase scoring.** A query of
only common words — "what do you do?" — has no BM25 signal at all, since
those words appear in every entry and carry no IDF. Phrase scoring sees them.

**Phrase scoring is plain Dice, not IDF-weighted.** Weighting by IDF reads a
rare phrasing as *distinctive*, so "tell me about" scores highly precisely
because few entries contain it. That is backwards.

**A phrase match requires substantive overlap.** Without that guard,
"what is 2+2" scores 0.57 against "what is your job" on the shared "what is"
alone. Every query beginning "what is" would match.

## Adding stopwords

`STOPWORDS` in `text.py`. Before adding a word, check it is not meaningful in
some corpus: "about" is filler in "tell me about X" and content in "an about
page". When a word is both, the usual answer is to add it and rely on aliases
for the cases where it carried meaning.

## Things to discuss first

Open an issue before building these, because they change what the library is:

- **Stemming or lemmatization.** Would help recall and needs a dependency or
  a hand-written stemmer, so it would have to be optional.
- **A synonym map.** Would close the biggest documented limitation — that
  "role" does not match "job" — without a model.
- **Non-English tokenization.** `normalize` assumes whitespace-delimited
  words, which does not hold for every language.

## What will not be merged

- A dependency in the core package. Zero dependencies is the point.
- A scoring change with no test for what it must still refuse.
