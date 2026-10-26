# How scoring works

Every entry gets a score between 0 and 1, and the best one wins if it clears
the threshold. The score is the **higher of two measures**, not a blend:

```python
max(bm25_score, phrase_score)
```

Two measures because they fail on opposite inputs, and taking the better of
the two means a query only has to be recognizable to one of them.

## BM25, for questions worded differently

BM25 ranks by how informative the shared words are. A word in every entry
carries no signal; a word in one entry carries a lot. That is what lets
"notice period" find *"What is your notice period?"* without the phrasing
matching:

```
notice period              high    ← shares both informative words
when can you start         1.000   ← an alias, matched as a whole phrase
tell me about the weather  0.000   ← no informative word in common
```

The exact figures depend on the whole index: IDF weighs a term by how rare
it is *here*, so adding an entry changes every score a little. Only a
saturated phrase match is fixed, at 1.000.

Three parts to it, each with a constant on the [tuning](tuning.md) page:

**Inverse document frequency** weights a term by how rare it is across the
index, with the `+1` guard so a term present in everything scores zero rather
than going negative.

**Term frequency saturation** stops repetition dominating. A query that says
"rates rates rates" is not three times more about rates.

**A length penalty** keeps a long entry from winning on sheer surface area —
it has more words, so it has more chances to overlap by accident.

## Phrase overlap, for questions worded the same

BM25 works on bags of words, so it cannot tell *"how much do you charge"*
from *"how much do you charge for a charge"*. The phrase measure compares the
query against each question and alias as a whole, which is what makes an
exact or near-exact phrasing score 1.000:

```
when can you start         1.000      ← an alias, matched as a phrase
how much do you charge     1.000      ← likewise
```

Those two are exact because a whole-phrase match saturates; the BM25 side of
the same query would score lower and lose the `max`.

This is why [aliases](aliases.md) do most of the work: each one is another
phrase that can match exactly.

## Why the maximum rather than a sum

A sum would let two weak signals add up to a confident answer, which is the
shape of a plausible wrong answer — the failure this library most needs to
avoid. The maximum means an entry has to be *convincingly* right by at least
one measure. A query that is vaguely like everything scores low against
everything.

## Normalization comes first

Both measures see normalized tokens, not raw text:

```python
normalize("What is your Notice Period?")      # ['notice', 'period']
query_terms("What is your notice period?")    # ['notice', 'period']
```

Case folded, punctuation dropped, and 109 stopwords removed — so *"what is
your"* contributes nothing and cannot make two unrelated questions look
similar. `normalize(text, keep_stopwords=True)` keeps them, for a caller who
needs the whole token stream.
