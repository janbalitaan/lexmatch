# Security

## Reporting

Email **janjanbalitaan@gmail.com** with what you found and how to reproduce
it. Please do not open a public issue for something exploitable until there
is a fix to go with it.

No bounty, and no promise of a timeline beyond this: you will get a reply
saying whether it is being worked on.

## What this library is responsible for

It ranks text against text. It opens no files, makes no network calls, runs
no subprocesses, executes nothing it was given, and has no dependencies — so
the surface is the Python it ships and nothing underneath.

That said, two things are worth stating.

### Untrusted queries are expected

A query is arbitrary text from whoever is asking, which is the normal case:
this exists to answer questions from the public. Nothing in a query is
evaluated, interpolated into anything, or used to build a pattern. The worst
a hostile query can do is score badly.

**Regular expressions are not built from input.** Tokenization uses fixed
patterns, so there is no input that makes matching backtrack catastrophically.
Query length bounds the work linearly.

### Untrusted entries are not

`Entry.answer` is returned **verbatim** to whoever asked. If entries come
from somewhere you do not control — a database other people write to, a file
in a repository that takes pull requests — then an answer is user-generated
content and has to be escaped by whatever renders it. This library does not
escape HTML, and should not: it does not know where the text is going.

The same holds for `question` and `aliases`, which are matched but not
returned.

## What it does not do

**It does not authenticate or rate-limit.** An index answers whoever calls
it, as many times as they call. Both belong in the layer that receives the
request.

**It does not log.** Nothing here records a query, so nothing here leaks one.
If your application logs questions, that log is personal data and its
retention is your decision.

**It has no cryptography**, no secrets, and nothing to rotate.

## Versions

Fixes go to the latest minor version. There is no long-term support branch;
the library is small enough that upgrading is cheap.
