# Small talk

A bot that refuses "thanks!" reads as broken in a way that a bot refusing an
obscure question does not. The visitor knows they said something ordinary, so
the failure looks like the bot rather than like the question.

```python
from lexmatch import Index, SmallTalk

index = Index([
    *SmallTalk.entries({
        "greeting": "Hello. Ask me anything about Jan's work.",
        "thanks": "You're welcome.",
        "farewell": "Take care.",
        "identity": "I'm a small bot that answers questions about Jan.",
        "capability": "Try asking about remote work, rates or availability.",
        "wellbeing": "Well, thanks. What would you like to know?",
    }),
    *my_entries,
])
```

```
'hi'               1.000   Hello. Ask me anything about Jan's work.
'hey there'        0.953   Hello. Ask me anything about Jan's work.
'thanks!'          1.000   You're welcome.
'who are you'      1.000   I'm a small bot that answers questions about Jan.
'what can I ask'   1.000   Try asking about remote work, rates or availability.
'cheers'           1.000   You're welcome.
'are you a bot'    1.000   I'm a small bot that answers questions about Jan.
```

## Why the phrasings ship and the replies do not

How somebody says hello is the same everywhere — "hiya" is "hiya" whatever
the index is about — so the phrasings are shipped and maintained here.

What the bot says back is not. It depends on whose bot it is, what it is for,
and how formal it should sound. So the replies come from you, and nothing is
answered until they do. There are no default answers to forget to change.

## The intents

| | |
| --- | --- |
| `greeting` | hello, hi, hiya, hey, good morning, howdy, yo |
| `farewell` | goodbye, bye, see you, later, take care, that is all |
| `thanks` | thanks, thank you, much appreciated, cheers, ta |
| `identity` | who are you, are you a bot, are you human, are you an ai |
| `capability` | what can you do, what can i ask, help, how does this work |
| `wellbeing` | how are you, how is it going, you ok |

Give a reply for the ones you want. An intent with no reply is simply not
added, so handling only greetings handles only greetings.

An unknown intent **raises**:

```
SmallTalkError: no such small-talk intent: greetings.
Available: greeting, farewell, thanks, identity, capability, wellbeing
```

Rather than being ignored — a typo there leaves the handler silently absent,
which looks exactly like one that works right up until somebody says hello.

## It stays out of the suggestions

`suggestions()` skips small-talk entries. Offering "hello" and "thanks" to
somebody whose question could not be answered is worse than offering
nothing: it reads as not having understood that they asked a question at all.

They are recognized by the `smalltalk` tag that `SmallTalk.entries` sets, so
an entry you tag yourself is skipped too.

## Extending the phrasings

```python
greeting = SmallTalk.phrasings_for("greeting")
Entry(question=greeting[0], answer="Hello!", aliases=[*greeting[1:], "aloha", "salut"])
```

The shipped phrasings are a starting point, not a boundary. Build the entry
yourself when you want more.


## Small talk answers small talk, and nothing else

A social phrasing is short, and the length penalty favours short entries, so
an entry built from "take care" or "good morning" would otherwise win any
message containing "care" or "good". Measured over fifteen simulated visitors,
five real questions were answered with a pleasantry:

```
'is the pay good'                        ->  "Hello."       1.000
'do you care about the frontend at all'  ->  "Take care."   0.957
'hi do u do consulting'                  ->  "Hello."       0.915
```

So a small-talk entry may only answer when every substantive word in the
message is one its own phrasings use. `hello` and `yo` pass. `hi do you do
consulting` does not, because `consulting` is in none of the greeting
phrasings — and holding the greeting back is what lets the consulting entry
answer instead.

Which entries this applies to is `SMALL_TALK_TAG`, the tag `SmallTalk.entries`
adds. Tag your own entries with it to get the same treatment:

```python
from lexmatch.constants import SMALL_TALK_TAG

Entry(
    question="no problem",
    answer="Any time.",
    aliases=["no worries", "all good"],
    tags=[SMALL_TALK_TAG, "acknowledgement"],
)
```

### Acknowledgements

An acknowledgement is social rather than substantive, so it neither holds back
small talk nor counts as a question of its own. "great, thanks!" is one unit —
a comma is not a terminator — and answering it with "You're welcome." while
reporting "great" as unanswered made a wholly correct reply look like a
partial failure.

`QuestionSplitter.ACKNOWLEDGEMENTS` holds the set, and replacing it changes
what counts:

```python
from lexmatch import QuestionSplitter

QuestionSplitter.ACKNOWLEDGEMENTS = frozenset({"great", "ta", "nice one"})
```

A word in the set only counts when it is the whole part. "is the pay good" is
one question, not an acknowledgement, because "good" is inside a sentence.
