# lexmatch

BM25 question matching with phrase scoring, and no dependencies.

[![PyPI](https://img.shields.io/pypi/v/lexmatch)](https://pypi.org/project/lexmatch/)
[![Python](https://img.shields.io/pypi/pyversions/lexmatch)](https://pypi.org/project/lexmatch/)
[![CI](https://github.com/janbalitaan/lexmatch/actions/workflows/ci.yml/badge.svg)](https://github.com/janbalitaan/lexmatch/actions/workflows/ci.yml)
[![License](https://img.shields.io/pypi/l/lexmatch)](https://github.com/janbalitaan/lexmatch/blob/main/LICENSE)

```python
from lexmatch import Entry, Index

index = Index([
    Entry("What do you do?", "I build backend services.",
          aliases=["what is your job", "what is your role"]),
    Entry("Are you open to remote work?", "Yes, and to relocation.",
          aliases=["remote", "relocate", "would you move"]),
])

entry, score = index.answer("what is your role")
# -> (Entry("What do you do?", ...), 1.0)

index.answer("what is the capital of France")
# -> (None, 0.0)      below the threshold, so it refuses
```

## When this beats embeddings

For a few dozen to a few thousand short question/answer pairs where the
answers are written by hand, a vector database is more machinery than the
problem deserves — a model to build the embeddings, a store to query them, and
a deployment that depends on both.

Lexical scoring needs none of that, runs in microseconds, and has a property
embeddings lack: **you can predict what it will match**, because the math is
legible. For an FAQ or a help desk, being able to explain why a question
matched is often worth more than a few points of recall.

Use embeddings when you need paraphrase matching across a large, unseen
corpus. Use this when you wrote the corpus yourself.

## Two things it adds to plain BM25

**Phrase scoring.** BM25 cannot rank a query made entirely of stopwords —
`"what do you do?"` — because those words appear in every entry and carry no
IDF. So phrasing is scored separately, with one guard: a phrase match only
counts when the substantive words overlap. Without that, `"what is 2+2"`
scores 0.57 against `"what is your job"` on `"what is"` alone.

**A refusal threshold.** Below `DEFAULT_THRESHOLD` (0.45), `answer()` returns
`None`. For question answering this matters more than ranking — an off-topic
question scores 0.2–0.4 from shared filler words, and a confident wrong answer
is worse than no answer. Scores are scaled to 0–1, so a threshold means the
same thing whatever the corpus size.

## Aliases do the heavy lifting

```python
Entry("Are you open to remote work?", "Yes.",
      aliases=["remote", "relocate", "would you move", "hybrid"])
```

Listing how people actually ask is the cheapest accuracy you can buy. Aliases
are weighted as heavily as the question itself.

## Tuning

| Setting | Default | Effect |
| --- | --- | --- |
| `threshold` | `0.45` | Higher refuses more. |
| `TERM_FREQUENCY_SATURATION` | `1.4` | Above this, repeating a term stops helping. |
| `LENGTH_PENALTY` | `0.72` | How much long entries are discounted. |

## Install

```bash
pip install lexmatch
```

Python 3.10+. No dependencies, so it runs in a serverless function, in CI, or
on a Raspberry Pi with no install step.

## License

MIT
