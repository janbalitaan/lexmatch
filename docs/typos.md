# Typos

A lexical matcher is unforgiving about spelling in a way that reads as
stupidity. `'whats your raets'` scored **0.000** and was refused, while a
person reading it would answer without noticing the typo.

Nothing about [aliases](aliases.md) or [synonyms](synonyms.md) helps, because
a misspelling is not a word anybody would think to declare. So an
unrecognized token is compared against the vocabulary the index actually
contains:

```
query                 before    after
'whats your raets'    0.000     0.723
'remte work'          0.553     1.000
'notce period'        0.000     1.000
'availabilty'         0.000     1.000
'pricng'              0.000     0.978
```

On by default. Nothing to configure for the common case.

## Why it corrects toward the index

The vocabulary is the index's own terms, not a dictionary. A query can only
ever be corrected toward something this index could answer — so a typo
becomes a word that exists *here*, and a word that exists nowhere here stays
as it is and scores nothing.

That is also why it does not need a word list, a model, or a dependency.

## Only unrecognized tokens

A token already in the vocabulary is left exactly as it is. Correction never
overrides a real word, because the real word is better evidence than any
similarity score:

```
senior      -> senior        (in the vocabulary; untouched)
junior      -> junior
rust        -> rust
writing     -> writing
```

## Three guards

A wrong correction answers a question nobody asked, which is worse than
refusing one somebody did. So:

**Short tokens are skipped.** Below four characters almost everything is
within one edit of everything, so `api` would "correct" to `and` and a
question about an API would be answered as a conjunction.

**The bar is high.** 0.8 similarity over the whole token, roughly one edit in
five characters. `rateing` does not become `rates` — it scores 0.667, and the
conservative reading is to leave it.

**A tie is left alone.** Exactly one candidate has to be closest. Two equally
close means the word is ambiguous, and guessing picks wrong half the time.

## It does approximate stemming, as a side effect

`remotely` is not in the vocabulary and is 0.857 similar to `remote`, so it
corrects — and a query of "can I work remotely" goes from 0.469 to 1.000.

That is a real improvement and worth knowing about, because this library
otherwise [does no stemming](limitations.md) and the correction pass is the
only thing that bridges a word form. It is approximate: `hiring` and `hire`
are 0.727 similar and will not bridge, while `availabilty` and `available`
will.

Do not rely on it for word forms. Write the alias.

## Turning it off

```python
Index(entries, tuning=Tuning().with_corrections(enabled=False))
```

For an index whose vocabulary is deliberately close together — product codes,
part numbers, SKUs — where every token is one edit from another and
correcting is guessing.

```python
Tuning().with_corrections(similarity=0.9)       # correct less
Tuning().with_corrections(minimum_length=6)     # only longer words
```
