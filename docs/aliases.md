# Aliases

An alias is another way somebody might ask the same question. They do more
for accuracy than any amount of tuning, because they give the phrase scorer
something to match exactly.

```python
Entry(
    question="Are you open to remote work?",
    answer="Yes, and I have done it for six years.",
    aliases=["work from home", "distributed team", "wfh"],
)
```

## What they buy, measured

The same entry, with and without:

```
query                  no aliases        with aliases
'work from home'       0.955  answered   1.000  answered
'wfh'                  0.000  refused    1.000  answered
'distributed team'     0.000  refused    1.000  answered
```

`wfh` shares no word with *"Are you open to remote work?"* — no amount of
threshold tuning reaches it, because there is nothing to score. An alias is
the only thing that can.

`work from home` was already answered without aliases, because it shares
three substantive words with the question. `wfh` shares none — no threshold
reaches it, because there is nothing to score. An alias is the only thing
that can.

## Writing them

**Write how people ask, not synonyms of your wording.** "wfh" is how somebody
types it. "telecommuting arrangements" is how a thesaurus would.

**One phrase per alias.** They are matched whole, so `["remote", "work from
home"]` gives two phrases that can each match exactly, while `["remote work
from home"]` gives one that matches neither.

**Short aliases are strong.** A one or two word alias matches a terse query
exactly and saturates at 1.000. That is usually how a real question arrives.

**Add the misses, do not lower the threshold.** `score()` shows what a query
scored; a question that should match and scored near zero is an alias you
have not written.

```python
for value, entry in index.score("wfh")[:3]:
    print(f"{value:.3f}  {entry.question}")
```

## They are matched, not stored as answers

An alias affects scoring only. The reply always comes from `entry.answer`, so
adding ten aliases does not mean maintaining ten answers.

An alias that normalizes to nothing — punctuation, or only stopwords — is
dropped when the index is built rather than kept as an empty phrase that
could match anything.

## A phrase alias still contributes its words

An alias is scored two ways: whole, by the phrase scorer, and word by word,
by BM25. So a multi-word alias adds **every one of its words** to the
entry's vocabulary, not just the phrase.

This surprises people, including the author of this page. An index with a
cost-reduction entry was missing *"what would you cost us"*, which is a
question about rate, so `"what would you cost"` went on the rate entry as a
phrase — expecting the phrase to be matched as a unit. Instead the bare word
`cost` joined the rate entry's terms, the two entries tied on it, and *"how
do you reduce cost"* — which had always worked — became ambiguous:

```
                             before          after the "fix"
'how do you reduce cost'     COST  1.000     ambiguous
'what would you cost us'     COST  1.000     ambiguous
```

One question gained nothing and another was lost.

So when you add a phrase alias, read its words one at a time and ask whether
each belongs on that entry. If one of them is the *other* entry's whole
subject, the alias will take that entry down with it.

Rephrasing the other entry to avoid the word does not fix it either — it just
moves which question is answered wrongly. `limitations.md` has the four
arrangements that were tried and the one that works, which is to let a single
entry own the word and answer both senses.
