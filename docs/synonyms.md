# Synonyms

[Aliases](aliases.md) attach a phrasing to one entry, which is right when the
phrasing belongs to that question. A **synonym** is for a word that means the
same thing everywhere.

```python
from lexmatch import Index, Tuning

index = Index(entries, tuning=Tuning().with_synonyms({
    "wfh": "work from home",
    "comp": "compensation",
    "ooo": "out of office",
}))
```

Writing `wfh` into the aliases of every entry that mentions remote work is
the same fact recorded five times, and the fifth entry is the one somebody
forgets. A synonym is declared once.

## What it buys, measured

Two entries with no aliases at all:

```
query            without synonyms      with
'wfh'            0.000  refused        0.624  answered
'comp'           0.000  refused        0.487  answered
'compensation'   0.974  answered       0.974  answered
```

Note the third row: adding a synonym for `comp` does not weaken the match for
the word it expands to.

## How expansion works

**Both sides go through the same map.** Entry terms are expanded when the
index is built and query terms when it scores, so a short form in the query
meets a long form in the entry whichever one was written short.

**The original token is kept.** `comp` expands to `comp compensation`, not to
`compensation` alone, so a query of `comp` still matches an entry that
literally says "comp". Dropping it would trade one miss for another.

**One token at a time.** A multi-word *key* can never match, so
`{"work from home": "remote"}` raises rather than sitting in the map doing
nothing:

```
SynonymError: the synonym key 'work from home' is more than one word.
Expansion happens one token at a time, so a multi-word key can never
match — put the phrase in the entry's aliases instead.
```

That direction is the useful one anyway: the *value* may be a phrase, which
is how `{"wfh": "work from home"}` works.

## Synonyms or aliases

| | |
| --- | --- |
| A word that means the same thing index-wide | synonym |
| A whole phrasing of one question | alias |
| An abbreviation, an initialism, a spelling variant | synonym |
| A question somebody asks completely differently | alias |

Reach for a synonym when you would otherwise write the same alias into
several entries. Reach for an alias when the phrasing only makes sense for
one question.

## Keys are lower-cased

Matching happens on normalized tokens, so a capitalized key would look like
it worked while matching nothing. `{"WFH": "work from home"}` and
`{"wfh": ...}` are the same declaration.
