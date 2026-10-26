# Limitations

Two kinds of thing, and the difference matters.

**Properties of the approach.** Lexical matching cannot recognize a question
that shares no words with anything in the index. That does not get fixed by
tuning; it gets fixed by an alias, or by reaching for embeddings.

**Bounds with a lever.** A threshold, a stopword list in one language, a
scoring constant. Each has a parameter, named in [tuning](tuning.md).

## It matches words, not meaning

*"Do you work from your house?"* and *"Are you open to remote work?"* share
nothing but stopwords. No threshold finds that, because there is no signal to
find — the score is 0.000, not 0.3.

Three options, in the order worth trying:

**Write the alias.** It takes a second and it is exact. For a question set
you control, this handles nearly everything.

**Accept the refusal.** `suggestions()` turns it into a menu, and a visitor
picking from three questions is a better outcome than a confident wrong
answer.

**Use embeddings.** If queries are genuinely open-ended and you cannot
enumerate the phrasings, this is the wrong tool. `sentence-transformers` and
a vector store will recognize paraphrase; they will also cost you a model
download, a few hundred megabytes of memory, and a slower cold start. That
trade is worth making when the question set is unbounded and not when it is a
FAQ.

## One language's worth of stopwords

The 77 shipped stopwords are English. For another language the list is wrong
in both directions — it removes nothing it should and keeps everything it
should not:

```python
Tuning().with_stopwords(["el", "la", "de", "que", "y"])
```

Replacing the list is a one-liner, but somebody has to write it. There is no
language detection here and none planned: guessing wrong would silently
change what every query matches.

## No stemming

*"consulting"* and *"consultant"* are different tokens. A query using one
will not match an entry using the other unless an alias bridges them.

Deliberate rather than missing. A stemmer is another dependency and another
source of surprise — Porter stemming turns "university" and "universe" into
the same token — and for a question set you control, an alias is both cheaper
and exact.

## One shared word can carry a wrong match

Phrase overlap is weighted by inverse document frequency, so filler no longer
decides a match. A single *substantive* word still can, and in an index whose
entries cover related subjects that is where the remaining errors are.

Measured against an index of twenty-five entries, asked by simulated people in
eleven professional roles:

```
'how do you decide when to refactor'  ->  "How do you decide build versus buy?"
'what dashboards do you build'        ->  "How do you decide build versus buy?"
'would you be a technical cofounder'  ->  "How do you approach technical debt?"
'have you built something from zero'  ->  "How do you decide build versus buy?"
```

Each shares exactly one content word with the entry it matched — *decide*,
*build*, *technical* — and nothing with the entry a person would have picked.
No threshold separates these from correct matches at the same score, because
the signal that would separate them is what the words *mean*.

Raising `minimum_overlap` to 2 removes them along with every correct one-word
match, which is worse. The fix that works is an alias on the entry that should
have won, which is what `unanswered()` is for: it reports what was asked and
missed, and an alias closes it for good.

## A question of pure filler can still be answered

A query with no substantive words is deliberately allowed to match on filler,
because filler is all it has — that is what makes "how are you" and "who are
you" work. The cost is that a *fragment* of filler is also answered:

```
'what is your'   ->  0.662, answered
```

There is no lexical signal that separates an incomplete question from a
complete one made of the same kind of words. Raising the threshold above 0.662
would refuse real small talk, which is the worse trade.

## Scores are not comparable across indexes

A 0.769 in one index is not the same confidence as 0.769 in another. IDF
weighs a term by how rare it is *in that index*, so adding an entry changes
every score slightly. The threshold is a property of your index, found by
watching real queries, not a number portable between deployments.

That is also why this documentation quotes exact scores sparingly: only a
whole-phrase match is fixed, at 1.000.

## It ranks, it does not search

There is no inverted index, no incremental update, no persistence. `Index`
scores every entry against every query, which is linear. Measured:

| entries | one question | a compound message |
| --- | --- | --- |
| 100 | 0.22 ms | 0.46 ms |
| 1,000 | 2.1 ms | 4.7 ms |
| 5,000 | 11.7 ms | 24.0 ms |

Fine for a few hundred, which is what a FAQ is. Noticeable at a few thousand.
Wrong for a million — for that you want a search engine, not this.

The linear scan is inherent; the constant was not always. The query used to
be normalized, corrected and expanded once *per entry* rather than once per
query, and `respond()` decided between the strict and loose readings twice
over — together 2.5x the work for no benefit.
