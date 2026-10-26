"""`SMALL_TALK_TAG` is the marker, so a custom set can opt in."""

from __future__ import annotations

from typing import ClassVar

import pytest

from lexmatch import Entry, Index, SmallTalk
from tests.social.small_talk_stays_in_its_lane import REPLIES


@pytest.fixture
def index() -> Index:
    return Index(
        [
            *SmallTalk.entries(REPLIES),
            Entry(
                question="What are your rate expectations?",
                answer="RATE",
                aliases=["rate", "pay", "salary"],
            ),
            Entry(
                question="Do you work on the frontend?",
                answer="FRONTEND",
                aliases=["frontend", "ui work"],
            ),
            Entry(
                question="Do you do consulting?",
                answer="CONSULTING",
                aliases=["consulting", "advisory"],
            ),
        ]
    )


class TestTheTagIsWhatDecides:
    """`SMALL_TALK_TAG` is the marker, so a custom set can opt in."""

    CUSTOM: ClassVar[list[Entry]] = [
        Entry(
            question="no problem",
            answer="SOCIAL",
            aliases=["np at all"],
            tags=["smalltalk", "custom"],
        ),
        Entry(question="What is your rate?", answer="RATE", aliases=["rate"]),
    ]

    def test_a_custom_tagged_entry_is_suppressed_too(self):
        index = Index(self.CUSTOM)
        assert index.reply("what is your rate").entry.answer == "RATE"

    def test_an_untagged_entry_is_not_suppressed(self):
        plain = [
            Entry(question="no problem", answer="SOCIAL", aliases=["np at all"]),
            Entry(question="What is your rate?", answer="RATE", aliases=["rate"]),
        ]
        index = Index(plain)
        assert index.reply("no problem").entry.answer == "SOCIAL"

    def test_the_tagged_one_still_answers_its_own_phrasing(self):
        assert Index(self.CUSTOM).reply("no problem").entry.answer == "SOCIAL"
