"""JSON: a bare list is read."""

from __future__ import annotations

import json

from lexmatch import Index, JsonParser
from tests.parsers.json_is_read import ROWS


class TestABareListIsRead:
    def test_every_entry_is_built(self):
        assert len(JsonParser.parse(json.dumps(ROWS))) == 2

    def test_the_fields_arrive(self):
        first = JsonParser.parse(json.dumps(ROWS))[0]
        assert first.question == "How do I reset my password?"
        assert first.answer == "Use the Forgot password link."
        assert first.aliases == ["forgot password", "locked out"]
        assert first.tags == ["account"]

    def test_the_result_is_an_index(self):
        index = Index(JsonParser.parse(json.dumps(ROWS)))
        assert index.reply("locked out").entry.answer == "Use the Forgot password link."

    def test_missing_optional_fields_are_empty(self):
        second = JsonParser.parse(json.dumps(ROWS))[1]
        assert second.aliases == []
        assert second.tags == []
