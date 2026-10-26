"""Reading a question set from a file rather than from Python.

A question set is content, and content is written by whoever owns it — in a
spreadsheet, a content system, a Markdown file in the same repository as the
rest of the documentation. Requiring it to be Python makes the person who
writes the answers depend on the person who writes the code, for every
change.

One parser per format, one class per file, each turning text into `Entry`
objects and raising `ParseError` with the line or key at fault rather than a
`KeyError` from somewhere inside.
"""

from __future__ import annotations

from lexmatch.parsers.csv_parser import CsvParser
from lexmatch.parsers.json_parser import JsonParser
from lexmatch.parsers.markdown_parser import MarkdownParser

__all__ = ["CsvParser", "JsonParser", "MarkdownParser"]
