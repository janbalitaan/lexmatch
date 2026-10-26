"""Questions as CSV, which is what a spreadsheet exports."""

from __future__ import annotations

from collections.abc import Sequence
import csv
import io
from pathlib import Path
from typing import ClassVar

from lexmatch.exceptions import ParseError
from lexmatch.models.entry import Entry


class CsvParser:
    """Reads a header row and one entry per row after it.

    A spreadsheet is where most question sets actually live, and exporting
    one is a single menu item. The header names the columns, so the order
    does not matter and extra columns are ignored.

    Aliases and tags hold several values in one cell, separated by `SEPARATOR`
    — a semicolon rather than a comma, because a comma inside a quoted CSV
    field is the one thing every hand-rolled splitter gets wrong.
    """

    #: Column names, lowercased before matching so "Question" works too.
    FIELDS: ClassVar[dict[str, tuple[str, ...]]] = {
        "question": ("question", "q", "prompt"),
        "answer": ("answer", "a", "response"),
        "aliases": ("aliases", "alias", "variants", "also asked"),
        "tags": ("tags", "tag", "category", "categories"),
    }

    #: What separates several aliases inside one cell.
    SEPARATOR: ClassVar[str] = ";"

    @classmethod
    def parse(cls, text: str) -> list[Entry]:
        """Build entries from CSV text."""
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            raise ParseError("the file is empty, so it has no header row")
        columns = cls._columns(reader.fieldnames)
        if "question" not in columns or "answer" not in columns:
            found = ", ".join(repr(name) for name in reader.fieldnames)
            raise ParseError(
                f"the header needs a question column and an answer column; found {found}"
            )
        entries: list[Entry] = []
        # Two, because a human counting lines in a spreadsheet starts at one
        # and the header is the first of them.
        for line, row in enumerate(reader, start=2):
            if not any((value or "").strip() for value in row.values()):
                continue
            entries.append(cls._entry_from(row, columns, line))
        return entries

    @classmethod
    def read(cls, path: Path | str) -> list[Entry]:
        """Build entries from a CSV file."""
        try:
            text = Path(path).read_text(encoding="utf-8-sig")
        except OSError as error:
            raise ParseError(f"cannot read {path}: {error.strerror}") from error
        return cls.parse(text)

    @classmethod
    def _columns(cls, fieldnames: Sequence[str]) -> dict[str, str]:
        """Map each field to the column it was found in."""
        lowered = {(name or "").strip().lower(): name for name in fieldnames}
        found: dict[str, str] = {}
        for field, accepted in cls.FIELDS.items():
            for candidate in accepted:
                if candidate in lowered:
                    found[field] = lowered[candidate]
                    break
        return found

    @classmethod
    def _entry_from(cls, row: dict, columns: dict[str, str], line: int) -> Entry:
        def cell(field: str) -> str:
            column = columns.get(field)
            return (row.get(column) or "").strip() if column else ""

        try:
            return Entry(
                question=cell("question"),
                answer=cell("answer"),
                aliases=cls._split(cell("aliases")),
                tags=cls._split(cell("tags")),
            )
        except Exception as error:
            raise ParseError(f"line {line}: {error}") from error

    @classmethod
    def _split(cls, cell: str) -> list[str]:
        """Split one cell into several values."""
        if not cell:
            return []
        return [part.strip() for part in cell.split(cls.SEPARATOR) if part.strip()]
