"""Questions as JSON, which is what an export or an API returns."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, ClassVar

from lexmatch.exceptions import ParseError
from lexmatch.models.entry import Entry


class JsonParser:
    """Reads a list of question objects, or an object wrapping one.

    Both shapes are accepted because both are what people have:

        [{"question": "...", "answer": "...", "aliases": ["..."]}]
        {"entries": [...]}

    Keys beyond the four an `Entry` has are ignored rather than refused, so a
    file carrying an id, a category or a last-updated stamp for some other
    system still loads.
    """

    #: The keys an entry is read from. Replace to read a file whose columns
    #: are named differently without rewriting it.
    FIELDS: ClassVar[dict[str, str]] = {
        "question": "question",
        "answer": "answer",
        "aliases": "aliases",
        "tags": "tags",
    }

    #: Keys that may wrap the list, tried in order.
    WRAPPERS: ClassVar[tuple[str, ...]] = ("entries", "questions", "faq", "items", "data")

    @classmethod
    def parse(cls, text: str, strict: bool = True) -> list[Entry]:
        """Build entries from JSON text.

        `strict=False` skips an entry that cannot be built instead of
        raising, for a file being edited while it is served. A malformed
        document is always an error, because then there is nothing to skip.
        """
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError as error:
            raise ParseError(
                f"not valid JSON: {error.msg} at line {error.lineno}, column {error.colno}"
            ) from error
        return cls._entries_from(cls._unwrap(loaded), strict=strict)

    @classmethod
    def read(cls, path: Path | str, strict: bool = True) -> list[Entry]:
        """Build entries from a JSON file."""
        return cls.parse(_read_text(path), strict=strict)

    @classmethod
    def _unwrap(cls, loaded: Any) -> list[Any]:
        """Find the list, whether it is the document or inside it."""
        if isinstance(loaded, list):
            return loaded
        if isinstance(loaded, dict):
            for wrapper in cls.WRAPPERS:
                found = loaded.get(wrapper)
                if isinstance(found, list):
                    return found
            offered = ", ".join(repr(key) for key in cls.WRAPPERS)
            raise ParseError(
                f"a JSON object needs one of {offered} holding the list of "
                f"entries; got keys {sorted(loaded)[:8]}"
            )
        raise ParseError(
            f"expected a list of entries or an object wrapping one, got {type(loaded).__name__}"
        )

    @classmethod
    def _entries_from(cls, rows: list[Any], strict: bool = True) -> list[Entry]:
        entries: list[Entry] = []
        for position, row in enumerate(rows):
            try:
                if not isinstance(row, dict):
                    raise ParseError(
                        f"entry {position} is a {type(row).__name__}, not an object"
                    )
                entries.append(cls._entry_from(row, position))
            except ParseError:
                if strict:
                    raise
        return entries

    @classmethod
    def _entry_from(cls, row: dict, position: int) -> Entry:
        fields = cls.FIELDS
        try:
            return Entry(
                question=str(row.get(fields["question"], "")),
                answer=str(row.get(fields["answer"], "")),
                aliases=_as_strings(row.get(fields["aliases"]), position, "aliases"),
                tags=_as_strings(row.get(fields["tags"]), position, "tags"),
            )
        except ParseError:
            raise
        except Exception as error:
            raise ParseError(f"entry {position}: {error}") from error


def _as_strings(value: object, position: int, field: str) -> list[str]:
    """Read a list of strings, accepting a single string as a list of one."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    raise ParseError(
        f"entry {position}: {field} should be a list of strings, got {type(value).__name__}"
    )


def _read_text(path: Path | str) -> str:
    """Read a file, reporting the path when it cannot be read."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise ParseError(f"cannot read {path}: {error.strerror}") from error
