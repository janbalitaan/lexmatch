"""JSON: reading a file."""

from __future__ import annotations

import json

import pytest

from lexmatch import JsonParser, ParseError
from tests.parsers.json_is_read import ROWS


class TestReadingAFile:
    def test_a_file_is_read(self, tmp_path):
        path = tmp_path / "faq.json"
        path.write_text(json.dumps({"entries": ROWS}), encoding="utf-8")
        assert len(JsonParser.read(path)) == 2

    def test_a_missing_file_names_the_path(self, tmp_path):
        with pytest.raises(ParseError, match="cannot read"):
            JsonParser.read(tmp_path / "absent.json")
