# Stemming

*"consulting"* and *"consult"* are different words to a lexical matcher. So
are *"built"* and *"build"*, *"rates"* and *"rate"*, *"designed"* and
*"design"*. Without folding them together, a query using one form cannot
reach an entry using the other, and the gap is invisible — nobody reports
being unanswered.

For a long time this library did not fold them, on the grounds that an alias
is cheaper and exact for a question set you write yourself. That holds at
twenty entries. It stops holding at the scale a support or documentation
index runs at: nobody hand-writes aliases for every tense and plural across
four hundred entries, and the ones they forget are the ones that fail.

Measured across 133 questions from thirty-seven simulated askers — eleven
professional roles and fifteen people who were not hiring anyone — folding
inflections took the suite from **76.7% to 85.0%** and cut confidently wrong
answers from fourteen to three.

## What folds

Only inflection: the endings that mark number and tense without changing
what a word is about.

```
plural      rates, taxes, policies    ->  rate, tax, policy
verb        consulting, consulted     ->  consult
adverb      remotely, quickly         ->  remote, quick
irregular   built, led, paid, people  ->  build, lead, pay, person
```

Derivational endings are left alone. *"payment"* stays distinct from *"pay"*
and *"consultant"* from *"consult"*, because the difference between those is
usually the difference between two entries.

## What does not

This is deliberately **not** a Porter stemmer. Porter strips derivational
suffixes too, which merges words that mean different things — *"university"*
and *"universe"* both become `univers`, so an index about one answers
questions about the other. For a matcher whose job includes refusing what it
does not know, that is a bad trade.

A stem is never shown to anyone, so it does not have to be a word. It has to
be the *same* token for every inflection, which is what these rules give:

```
scale, scaling, scaled, scales        ->  scal
experience, experienced, experiences  ->  experienc
```

The trailing "e" comes off both sides rather than being restored, because the
rules that restore it get *"experienced"* wrong whichever way they are
written.

## Turning it off, or replacing it

```python
Tuning().with_stemmer(None)                  # exact word forms only
Tuning().with_stemmer(SnowballStemmer().stem) # or anything else
```

Any callable from a word to a token works, so a Snowball stemmer, a
lemmatizer or a domain-specific table drops in. Both the index and the query
go through the same one, so they always agree.

## Extending the rules

Three tables, all replaceable:

```python
from lexmatch.stemming import Stemmer

Stemmer.IRREGULAR = {**Stemmer.IRREGULAR, "spake": "speak"}
Stemmer.KEEP = Stemmer.KEEP | {"kudos", "jenkins"}
```

`IRREGULAR` holds the forms no suffix rule reaches. `KEEP` holds the words a
rule would damage — *"process"* is not the plural of *"proces"*, and
*"kubernetes"* is not the plural of anything. `SUFFIXES` holds the rules
themselves, tried in order.

One entry is worth knowing about: **`"building"` is not on `KEEP`**, so it
folds to `build`. In the indexes this serves it is far more often the verb
("how do you build a team") than the noun. For an index about premises, add
it back.

## The cost

Folding increases recall and increases false matches. The measured net is
strongly positive, but the failures it adds are real:

```
'do you like working alone'  ->  "Are you open to remote work?"  1.000
```

*"working"* folds to *"work"*, *"alone"* is a word the index has never seen,
and so the only content word left is one they share. `limitations.md` has the
two measured attempts at charging for an unknown word and why neither is the
default.
