"""JSON: what is refused."""

from __future__ import annotations

import json

import pytest

from lexmatch import JsonParser, ParseError
from tests.parsers.json_is_read import ROWS


class TestWhatIsRefused:
    def test_text_that_is_not_json_reports_where(self):
        with pytest.raises(ParseError, match="line 1"):
            JsonParser.parse("{not json")

    def test_a_document_that_is_not_a_list_or_object(self):
        with pytest.raises(ParseError, match="got str"):
            JsonParser.parse('"just a string"')

    def test_an_entry_that_is_not_an_object_names_its_position(self):
        with pytest.raises(ParseError, match="entry 1 is a str"):
            JsonParser.parse(json.dumps([ROWS[0], "not an object"]))

    def test_an_entry_with_no_question_names_its_position(self):
        with pytest.raises(ParseError, match="entry 0"):
            JsonParser.parse(json.dumps([{"answer": "A"}]))

    def test_aliases_of_the_wrong_shape_name_the_field(self):
        with pytest.raises(ParseError, match="aliases should be a list"):
            JsonParser.parse(json.dumps([{**ROWS[0], "aliases": {"a": 1}}]))
