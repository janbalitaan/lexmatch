"""The question set as content, not as code.

Whoever writes the answers should not need Python to change them. All three
formats are written here, read back, and queried — so you can see what the
file looks like and what comes out of it.

    python examples/06_from_a_file.py
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from lexmatch import CsvParser, Index, JsonParser, MarkdownParser, ParseError

CSV = """\
Question,Answer,Aliases,Category,Reviewed
How do I cancel my subscription?,"Settings, then Billing, then Cancel",cancel,billing,2026-01-04
Where are my invoices?,Settings then Billing then Invoices.,invoice;receipt,billing,2026-01-04

Do you offer a free trial?,Fourteen days on any plan.,trial;free trial,plans,2025-11-20
"""

JSON = """\
{"entries": [
  {"id": 41, "question": "How do I reset my password?",
   "answer": "Use the Forgot password link on the sign-in page.",
   "aliases": ["forgot password", "locked out"], "tags": ["account"]},
  {"id": 42, "question": "How do I add a teammate?",
   "answer": "Settings, then Team, then Invite.",
   "aliases": "add user", "tags": ["account"]}
]}
"""

MARKDOWN = """\
# Support

## What are your support hours?

Nine to six, Monday to Friday, UK time.

*Also asked: hours, when are you open, support times*

#support

## Do you have an API?

Yes, documented at example.com/api.

*Also asked: api, integrate, webhooks*

#developers
"""

PROBES = [
    "how do i cancel",
    "where can i find my receipts",
    "is there a free trial",
    "i'm locked out",
    "how do i invite a colleague",
    "when are you open",
    "do you have webhooks",
]


def main() -> None:
    with TemporaryDirectory() as directory:
        folder = Path(directory)
        (folder / "faq.csv").write_text(CSV, encoding="utf-8")
        (folder / "faq.json").write_text(JSON, encoding="utf-8")
        (folder / "faq.md").write_text(MARKDOWN, encoding="utf-8")

        # One index out of three files. Each parser returns plain `Entry`
        # objects, so they combine with each other and with entries written
        # in Python.
        entries = [
            *CsvParser.read(folder / "faq.csv"),
            *JsonParser.read(folder / "faq.json"),
            *MarkdownParser.read(folder / "faq.md"),
        ]
        print(f"{len(entries)} entries from three files\n")
        for entry in entries:
            print(f"  {entry.question}")
            print(f"    aliases {entry.aliases}  tags {entry.tags}")
        print()

        index = Index(entries)
        print("Asking it things\n")
        for probe in PROBES:
            reply = index.reply(probe)
            answer = reply.entry.answer if reply.answered else "(no article)"
            print(f"  {probe:<32} {reply.score:.3f}  {answer}")

        print("\nWhen the file is wrong, the error says where\n")
        broken = folder / "broken.csv"
        broken.write_text(
            "question,answer\nWhat is this?,A bot.\n,orphaned\n", encoding="utf-8"
        )
        try:
            CsvParser.read(broken)
        except ParseError as error:
            print(f"  ParseError: {error}")

        broken.write_text("title,body\nsomething,else\n", encoding="utf-8")
        try:
            CsvParser.read(broken)
        except ParseError as error:
            print(f"  ParseError: {error}")


if __name__ == "__main__":
    main()
