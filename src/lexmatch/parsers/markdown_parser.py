"""Questions as Markdown, which is what a FAQ page already is."""

from __future__ import annotations

from pathlib import Path
import re
from typing import ClassVar

from lexmatch.exceptions import ParseError
from lexmatch.models.entry import Entry


class MarkdownParser:
    """Reads a heading as the question and the prose under it as the answer.

    A FAQ is usually already written as a Markdown page, which makes it the
    one format where the question set needs no separate copy to drift out of
    date:

        ## Are you open to remote work?
        Yes, and I have done it for six years.

        *Also asked: remote, work from home*

    Aliases come from an italic line beginning with one of `ALSO_ASKED`, which
    reads naturally on the rendered page rather than looking like
    configuration. Tags come from a line of `#hashtags`.
    """

    #: Which heading level starts an entry. Two by default, so the page can
    #: keep a single `#` title.
    LEVEL: ClassVar[int] = 2

    #: Openings for the aliases line, matched case-insensitively.
    ALSO_ASKED: ClassVar[tuple[str, ...]] = (
        "also asked",
        "also",
        "aliases",
        "variants",
    )

    _TAGS: ClassVar[re.Pattern[str]] = re.compile(r"^\s*(#\w[\w-]*(?:\s+#\w[\w-]*)*)\s*$")

    @classmethod
    def parse(cls, text: str) -> list[Entry]:
        """Build entries from Markdown text."""
        heading = re.compile(rf"^#{{{cls.LEVEL}}}\s+(?P<question>.+?)\s*$", re.MULTILINE)
        matches = list(heading.finditer(text))
        if not matches:
            raise ParseError(
                f"no level-{cls.LEVEL} headings found, so there are no questions. "
                f"Each entry starts with {'#' * cls.LEVEL} followed by the question"
            )
        entries: list[Entry] = []
        for position, match in enumerate(matches):
            ends = matches[position + 1].start() if position + 1 < len(matches) else len(text)
            body = text[match.end() : ends]
            line = text.count("\n", 0, match.start()) + 1
            entries.append(cls._entry_from(match.group("question"), body, line))
        return entries

    @classmethod
    def read(cls, path: Path | str) -> list[Entry]:
        """Build entries from a Markdown file."""
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as error:
            raise ParseError(f"cannot read {path}: {error.strerror}") from error
        return cls.parse(text)

    @classmethod
    def _entry_from(cls, question: str, body: str, line: int) -> Entry:
        answer: list[str] = []
        aliases: list[str] = []
        tags: list[str] = []
        for raw in body.splitlines():
            stripped = raw.strip()
            if not stripped:
                continue
            found = cls._aliases_in(stripped)
            if found is not None:
                aliases.extend(found)
                continue
            tag_match = cls._TAGS.match(stripped)
            if tag_match:
                tags.extend(part.lstrip("#") for part in tag_match.group(1).split())
                continue
            answer.append(stripped)
        try:
            return Entry(
                question=question.strip(),
                answer=" ".join(answer),
                aliases=aliases,
                tags=tags,
            )
        except Exception as error:
            raise ParseError(f"line {line}: {error}") from error

    @classmethod
    def _aliases_in(cls, stripped: str) -> list[str] | None:
        """Read an aliases line, or None when this is not one."""
        bare = stripped.strip("*_").strip()
        lowered = bare.lower()
        for opening in cls.ALSO_ASKED:
            if lowered.startswith(opening):
                rest = bare[len(opening) :].lstrip(":").strip()
                return [part.strip() for part in rest.split(",") if part.strip()]
        return None
