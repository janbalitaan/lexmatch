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
