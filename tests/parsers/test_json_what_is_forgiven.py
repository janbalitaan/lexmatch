"""JSON: what is forgiven."""

from __future__ import annotations

import json

from lexmatch import JsonParser
from tests.parsers.json_is_read import ROWS


class TestWhatIsForgiven:
    def test_unknown_keys_are_ignored(self):
        """A file carrying an id or a timestamp for another system."""
        rows = [{**ROWS[0], "id": 41, "updated": "2026-01-02", "owner": "ops"}]
        assert JsonParser.parse(json.dumps(rows))[0].question == ROWS[0]["question"]

    def test_a_single_string_is_read_as_a_list_of_one(self):
        rows = [{"question": "Q and A?", "answer": "A", "aliases": "refund"}]
        assert JsonParser.parse(json.dumps(rows))[0].aliases == ["refund"]

    def test_a_non_string_value_is_coerced(self):
        rows = [{"question": "How many?", "answer": 42}]
        assert JsonParser.parse(json.dumps(rows))[0].answer == "42"
