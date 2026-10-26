# Tuning

Every number the scorer uses is replaceable. The defaults suit a question set
of the size most people have — a few dozen entries of a sentence or two — and
the realistic reasons to move them are immediate: entries that are paragraphs
rather than questions, a domain whose vocabulary the stopword list eats, a bot
that should answer more or less readily.

```python
from lexmatch import Index, Tuning

index = Index(entries, tuning=Tuning(
    threshold=0.6,
    minimum_overlap=2,
))
```

`Tuning()` with no arguments equals the shipped constants exactly, so
adopting it changes nothing until you ask for a change. It is frozen, so an
index cannot have its scoring altered after it was built.

## The numbers

| | default | what it does |
| --- | --- | --- |
| `threshold` | 0.45 | the score an answer must clear. See [refusing](refusing.md) |
| `saturation` | 1.4 | how fast repeated terms stop adding. BM25's *k₁* |
| `length_penalty` | 0.72 | how much a long entry is penalized. BM25's *b* |
| `minimum_overlap` | 1 | substantive words a phrase must share before it scores |
| `ambiguity_margin` | 0.05 | how close a runner-up has to be to count as a tie |
| `ambiguity_floor` | 0.50 | how confident a tie has to be to be worth asking about |
| `stopwords` | 77 words | words carrying no signal |
| `synonyms` | none | words read as each other. See [synonyms](synonyms.md) |
| `corrections` | on | mistyped words read as real ones. See [typos](typos.md) |

**`saturation`** — lower makes the first occurrence of a term count for
almost everything; higher lets repetition keep adding. Raise it when entries
are long enough that term counts mean something, which for one-sentence
questions they do not.

**`length_penalty`** — 0 ignores entry length entirely, 1 applies it in full.
Lower it when entries are deliberately uneven in length and you do not want
the short ones favoured. The default leans toward shorter entries, which is
right when entries are questions and wrong when they are paragraphs.

**`minimum_overlap`** — how many substantive words a query and an entry must
share before the phrase scorer will consider them related at all. Raise it to
2 for an index whose entries share a lot of vocabulary.

With four entries all beginning *"What is your rate for…"*, a query of
*"what is your rate for consulting"* scores 0.139 at the default and 0.084 at
2, because sharing one diluted word is not enough to be sure:

```
minimum_overlap=1   0.139
minimum_overlap=2   0.084
```

Both are refused at the default 0.45 threshold, which is the more useful
lesson: in an index of near-duplicate entries, every shared word has a low
inverse document frequency, so **nothing scores well and no tuning fixes it**.
Four entries that differ by one word each are better written as one entry
with four aliases.

Its effect is often hidden, because BM25 usually wins the maximum when there
are substantive words in common. It decides when the phrase scorer would
otherwise win on thin overlap.

The guard does not apply to a query with no substantive words at all — see
the stopword note below, and `limitations.md`.

## Stopwords

Three ways to change them, because three different things go wrong:

```python
Tuning().with_stopwords(extra=["please", "kindly"])   # noise in this domain
Tuning().with_stopwords(keep=["can"])                 # a stopword that is content
Tuning().with_stopwords(["el", "la", "de"])           # another language
```

**`extra`** adds words that carry no signal here. A term in *every* entry
already scores zero through IDF, so this is for the merely frequent — a
product name, a politeness.

**`keep`** takes a word out of the list. "can" is a stopword and a tin;
"will" is a stopword and a legal document. Those queries score nothing until
the word counts as content.

**`stopwords`** replaces the list outright, for another language.

Applied in that order, so `extra` and `keep` act on whatever `stopwords` set.
A word in both is **kept**, because asking to keep a word is the more
specific instruction. Words are lower-cased, since matching happens on
normalized tokens and a capitalized entry would look like it worked while
matching nothing.

## Nonsense is refused at construction

```python
Tuning(threshold=-0.1)      # TuningError
Tuning(saturation=0)        # TuningError — divides by zero
Tuning(length_penalty=2)    # TuningError
Tuning(minimum_overlap=-1)  # TuningError
```

Raised when the tuning is built, not when scoring runs. A saturation of 0
would otherwise surface as an index that silently never matches, which reads
as "my questions are worded badly" rather than as a configuration error.

## Logging what is in force

```python
index.tuning.describe()
# threshold 0.45, saturation 1.4, length penalty 0.72
# minimum overlap 1, ambiguity margin 0.05, ambiguity floor 0.5
# unknown word cost 0.0, stemming on, morphology on, 137 stopwords
# 0 synonyms
# typo correction at 0.8 similarity, 4 characters and up
```

Counts the stopwords rather than listing them — a hundred and thirty-seven words in a log
line is noise.
