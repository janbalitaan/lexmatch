# Informal writing

Most of what a question box receives is not written the way documentation is.
It has contractions, no capitals, no final punctuation, and tag questions.
Three defects in how that was read cost more accuracy than anything else
measured — across twenty informally written questions, **65% answered before
these fixes and 95% after**, with every other benchmark unchanged.

## An apostrophe was splitting the word

The word pattern does not include an apostrophe, so it *split* on one:

```
"don't"    ->  ['don']          the "t" was dropped as too short
"you've"   ->  ['you', 've']
"what's"   ->  ['what']
```

The form people actually type was handled *worse* than the stripped form.
Apostrophes are now removed before splitting, straight and curly both — the
curly ones arrive from anything that autocorrects, which is most phones.

## A contraction was read as an unknown word

With the apostrophe gone, `dont` is a token in no stopword list and in no
entry. A word the index has never seen is the rarest kind of word there is,
so the weighting treated it as one of the most discriminating terms in the
query. Measured against a twenty-five entry index, `youv` scored 3.06 — the
same as the rarest real term there.

Each is now replaced by the words it stands for, and those are ordinary
stopwords:

```
dont   ->  do not
youve  ->  you have
whats  ->  what is
```

Expanding rather than listing the contracted forms as stopwords, because the
words are sometimes wanted: `"what is your rate"` needs its *what is* for
phrase scoring, and `"I don't need sponsorship"` needs its *not* for negation
to see.

Ambiguous forms are deliberately absent. *"ill"*, *"well"*, *"id"*, *"wed"*
and *"lets"* are words, and expanding them is wrong as often as it is right.
`Contractions.FORMS` is replaceable.

## A tag question is not a negative

This was the expensive one. English tag questions *confirm* the clause before
them:

```
'you've led teams before, haven't you?'   expects yes
'that works, doesn't it?'                 expects yes
```

The negation detector saw `haven't` and reported the match as negated, so
five of twenty questions matched **perfectly, at 1.000, and were thrown
away**. A negated auxiliary followed by a pronoun at the end of the message
is now read as affirmative.

The same for a polite request, which asks for the thing rather than denying
it:

```
"can't you start sooner?"        wants the notice period
"couldn't you reduce the cost?"  wants the cost answer
```

Only at the start of the message, so *"we can't afford that rate"* stays
negative. Both patterns are class attributes on `Negation` and can be
replaced.

A genuine negative is untouched: *"are you not open to remote work"*, *"you
never worked remotely"*, *"no longer available"*.

## How it is typed, not how it is written

`SmallTalk.PHRASINGS` gained the short forms people use: `thx`, `ty`, `tnx`,
`sup`, `are you a robot`, `bot or human`, `who made you`. A bot that refuses
*"thx"* reads as broken for the same reason one that refuses *"thanks"* does
— the visitor knows they said something ordinary, so the failure looks like
the bot rather than like the question.
