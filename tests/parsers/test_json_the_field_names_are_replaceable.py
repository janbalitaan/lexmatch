"""JSON: the field names are replaceable."""

from __future__ import annotations

import json

from lexmatch import JsonParser


class TestTheFieldNamesAreReplaceable:
    """So a file whose columns are named differently loads unchanged."""

    def test_renamed_fields_are_read(self):
        original = dict(JsonParser.FIELDS)
        try:
            JsonParser.FIELDS = {**original, "question": "prompt", "answer": "reply"}
            rows = [{"prompt": "What is this?", "reply": "A bot."}]
            entry = JsonParser.parse(json.dumps(rows))[0]
            assert entry.question == "What is this?"
            assert entry.answer == "A bot."
        finally:
            JsonParser.FIELDS = original

    def test_the_default_is_restored(self):
        assert JsonParser.FIELDS["question"] == "question"
