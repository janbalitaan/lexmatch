"""JSON: a wrapped list is read."""

from __future__ import annotations

import json

import pytest

from lexmatch import JsonParser, ParseError
from tests.parsers.json_is_read import ROWS


class TestAWrappedListIsRead:
    """Because an export usually wraps it."""

    @pytest.mark.parametrize("wrapper", ["entries", "questions", "faq", "items", "data"])
    def test_each_accepted_wrapper(self, wrapper):
        assert len(JsonParser.parse(json.dumps({wrapper: ROWS}))) == 2

    def test_an_unrecognized_wrapper_is_refused_by_name(self):
        with pytest.raises(ParseError, match="holding the list of entries"):
            JsonParser.parse(json.dumps({"rows": ROWS}))

    def test_the_message_names_what_was_accepted(self):
        with pytest.raises(ParseError, match="'entries'"):
            JsonParser.parse(json.dumps({"rows": ROWS}))
