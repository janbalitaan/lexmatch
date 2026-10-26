"""The stemmer is replaceable."""

from __future__ import annotations

from typing import ClassVar

from lexmatch import Entry, Index
from lexmatch.models.tuning import Tuning


class TestTheStemmerIsReplaceable:
    FORMS: ClassVar[list[Entry]] = [
        Entry(question="Do you do consulting?", answer="CONSULTING", aliases=["consulting"]),
        Entry(question="What is your notice period?", answer="NOTICE", aliases=["notice"]),
    ]

    def test_it_is_on_by_default(self):
        """So "do you consult" reaches the consulting entry."""
        assert Index(self.FORMS).reply("do you consult").entry.answer == "CONSULTING"

    def test_none_matches_exact_word_forms_only(self):
        """Both have to be off. Turning off the stemmer alone leaves
        `Morphology`, which bridges "consult" to "consulting" by prefix —
        a different mechanism reaching the same pair."""
        exact = Index(
            self.FORMS,
            tuning=Tuning().with_stemmer(None).with_morphology(None),
        )
        assert not exact.reply("do you consult").answered
        assert exact.reply("consulting").answered

    def test_morphology_alone_also_bridges_it(self):
        """So the test above is turning off two things for a reason."""
        stemless = Index(self.FORMS, tuning=Tuning().with_stemmer(None))
        assert stemless.reply("do you consult").answered

    def test_a_replacement_is_used(self):
        """Any callable from a word to a token, so a Snowball stemmer or a
        lemmatizer drops in."""
        shouty = Index(self.FORMS, tuning=Tuning().with_stemmer(str.upper))
        assert shouty.reply("CONSULTING").answered

    def test_describe_says_which(self):
        assert "stemming on" in Tuning().describe()
        assert "stemming off" in Tuning().with_stemmer(None).describe()
