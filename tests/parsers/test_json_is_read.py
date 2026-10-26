"""A question set as JSON, which is what an export or an API returns."""

from __future__ import annotations

import json

import pytest

from lexmatch import Index, JsonParser, ParseError

ROWS = [
    {
        "question": "How do I reset my password?",
        "answer": "Use the Forgot password link.",
        "aliases": ["forgot password", "locked out"],
        "tags": ["account"],
    },
    {"question": "What is your refund policy?", "answer": "Full refund within 14 days."},
]


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


class TestReadingAFile:
    def test_a_file_is_read(self, tmp_path):
        path = tmp_path / "faq.json"
        path.write_text(json.dumps({"entries": ROWS}), encoding="utf-8")
        assert len(JsonParser.read(path)) == 2

    def test_a_missing_file_names_the_path(self, tmp_path):
        with pytest.raises(ParseError, match="cannot read"):
            JsonParser.read(tmp_path / "absent.json")


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
