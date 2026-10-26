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

The 137 shipped stopwords are English. For another language the list is wrong
in both directions — it removes nothing it should and keeps everything it
should not:

```python
Tuning().with_stopwords(["el", "la", "de", "que", "y"])
```

Replacing the list is a one-liner, but somebody has to write it. There is no
language detection here and none planned: guessing wrong would silently
change what every query matches.

## Stemming folds inflection, not meaning

*"consulting"* and *"consult"* fold together; *"consultant"* does not, and
nor does *"payment"* with *"pay"*. Only inflectional endings are stripped,
because the derivational ones Porter also strips merge words that mean
different things — "university" and "universe" both become `univers`.

The cost of folding at all is a class of false match that exact forms would
have refused:

```
'do you like working alone'  ->  "Are you open to remote work?"  1.000
```

Measured net across 133 questions: 76.7% to 85.0%, with confidently wrong
answers falling from fourteen to three. `stemming.md` has the rules and how
to replace or disable them.

## An unknown word is invisible, and charging for it costs more

A word the index has never seen has no inverse document frequency, so it
contributes nothing to the score ceiling. A query is therefore satisfiable by
matching only the words it happens to share, however much of the question
was not understood:

```
'do you like working alone'           1.000   on "work" alone
'what dashboards do you build'        1.000   on "build" alone
'would you be a technical cofounder'  1.000   on "technical" alone
```

Two ways of charging for it were implemented and measured against 133
questions:

```
ignoring unknown words (the default)              85.0%
a linear cost on the unrecognized fraction        82.7%
counting them at a zero-document frequency,
which is the highest weight the formula gives     69.9%
```

Both are worse, and the reason is structural: in a question set small enough
to hand write, most words in a naturally phrased question are absent from
every entry — they are conversational, not substantive. Charging for an
unknown word charges for natural phrasing.

`Tuning.unknown_word_cost` is kept for the case where the trade runs the
other way: a deliberately narrow index where most of what it is asked is out
of scope, and a refusal is better than a guess.

## Two entries that mean different things by the same word

The clearest example of the ceiling. An index with both

```
What are your rate expectations?     aliases: rate, salary, compensation
How do you reduce cost?              aliases: cost, cloud spend, savings
```

answers *"what would you cost us"* with the cost-reduction entry. The asker
meant compensation; `cost` is the only content word, and it belongs to the
other entry.

Four arrangements were tried. **None separates the two questions**, because
whichever entry holds the word answers both of them:

```
                                   'what would      'how do you
                                    you cost us'     reduce cost'
cost on the reduction entry         COST   wrong     COST   right
cost phrase added to the rate       ambiguous        ambiguous
reduction entry avoids the word     RATE   right     RATE   wrong
```

The middle row is worth dwelling on, because it is the obvious fix and it
makes things worse: a phrase alias contributes its individual words, so
`"what would you cost"` puts the bare `cost` on the rate entry, the two tie,
and a question that had always worked stops working.

What does work is to stop pretending they are two questions. One entry owning
the word, whose answer covers both senses, is right every time:

```python
Entry(
    question="What do you cost?",
    answer="My rate is X. On cloud cost, I have done Y.",
    aliases=["rate", "salary", "what would you cost", "reduce cost", "cloud spend"],
)
```

This is an authoring decision and not a tuning one. A lexical matcher cannot
know that a chief executive costing a hire and an engineer asking about cloud
spend mean different things by one word — that comes from who is asking, and
nothing in the text carries it.

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
