# Reading a question set from a file

A question set is content. Content is written by whoever owns it — in a
spreadsheet, a content system, a Markdown page alongside the rest of the
documentation. Requiring it to be Python makes the person who writes the
answers depend on the person who writes the code, for every change.

Three parsers, one per format. Each returns `list[Entry]`, which is what
`Index` takes:

```python
from lexmatch import Index, CsvParser

index = Index(CsvParser.read("faq.csv"))
```

## CSV, which is what a spreadsheet exports

```
Question,Answer,Aliases,Category
How do I cancel my subscription?,"Settings, then Billing, then Cancel plan.",cancel;unsubscribe,billing
Where are my invoices?,Settings then Billing then Invoices.,invoice;receipt,billing
```

The header names the columns, so their order does not matter and extra
columns are ignored — an id, an owner, a last-reviewed date for some other
system. Names are matched without case, and `q`/`a` and `prompt`/`response`
are accepted as well as `question`/`answer`.

Several aliases go in one cell, separated by a **semicolon** rather than a
comma. A comma inside a quoted CSV field is the one thing every hand-rolled
splitter gets wrong, and the separator is `CsvParser.SEPARATOR` if a
semicolon is wrong for your data.

A blank row is skipped, because a spacer row and a trailing newline are both
normal. A row with an answer and no question is an error naming its line,
counted the way a spreadsheet counts — header included — so the number
matches what you see on screen.

## JSON, which is what an export or an API returns

```json
{"entries": [
  {"question": "How do I reset my password?",
   "answer": "Use the Forgot password link.",
   "aliases": ["forgot password", "locked out"],
   "tags": ["account"],
   "id": 41}
]}
```

A bare list works too. The wrapper may be `entries`, `questions`, `faq`,
`items` or `data`. Keys an `Entry` does not have are ignored, so a file
carrying ids and timestamps loads unchanged, and a single string where a list
is expected is read as a list of one.

`JsonParser.FIELDS` maps the four fields to key names, so a file using
`prompt` and `reply` loads without being rewritten.

## Markdown, which is what a FAQ page already is

```markdown
## Are you open to remote work?

Yes, and I have done it for six years.

*Also asked: remote, work from home, wfh*

#hiring #logistics
```

A level-two heading is the question and the prose under it is the answer, so
the page renders as documentation and loads as a question set — the one
format where there is no second copy to drift out of date.

Aliases come from a line opening with *Also asked*, *Also*, *Aliases* or
*Variants*, which reads as a note to the reader rather than as
configuration. Tags come from a line of `#hashtags`, or from one opening with
*Tags*, *Tagged* or *Categories*.

Italic and blockquote markup are both accepted, and so is neither, because
all three are how people write that note:

```markdown
*Also asked: remote, work from home*
> also: remote, work from home
> tags: work, current
```

A single `#` heading is the page title and not an entry, and
`MarkdownParser.LEVEL` changes which level is read. `ALSO_ASKED` and `TAGGED`
hold the opening words.

## When something is wrong with the file

Every parser raises `ParseError`, which carries where:

```
line 3: an entry needs a question; got '' (answer: 'orphaned')
entry 1 is a str, not an object
a JSON object needs one of 'entries', 'questions', ... ; got keys ['rows']
the header needs a question column and an answer column; found 'title', 'body'
no level-2 headings found, so there are no questions
```

A question set is usually long and often generated, so "something is wrong
with your file" costs whoever owns it an afternoon.

## A file somebody is editing

Every parser takes `strict`, which defaults to true:

```python
entries = MarkdownParser.read("answers.md")                 # raises
entries = MarkdownParser.read("answers.md", strict=False)   # skips
```

Strict is right for a file loaded once at startup — it should say what is
wrong rather than quietly hold fewer answers than it appears to.

It is wrong for a file being edited while it is served. A question set
reloaded on change should keep answering while its owner is halfway through
adding the next question, and a heading with nothing under it yet is what
halfway looks like. Raising there takes a working bot down over an unfinished
sentence.

What is always an error is something there is no way to skip past: JSON that
is not JSON, a CSV with no usable header, a Markdown page with no headings.

## What an entry must have

`Entry` refuses a blank question or a blank answer when it is built, rather
than letting it fail to match later. The two are indistinguishable
afterwards: an entry with a blank question scores zero against every query,
exactly as an entry about something nobody asks does. One is a broken
question set and the other is normal.

A blank *alias* is dropped rather than refused — an alias is optional by
nature, and a trailing empty column is what an export looks like.
