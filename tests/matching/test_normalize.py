"""TestNormalize."""

from __future__ import annotations

from lexmatch import normalize


class TestNormalize:
    def test_accents_fold(self):
        assert normalize("résumé") == normalize("resume")

    def test_stopwords_are_dropped_by_default(self):
        assert "the" not in normalize("the backend")

    def test_stopwords_can_be_kept(self):
        assert "the" in normalize("the backend", keep_stopwords=True)

    def test_technology_punctuation_survives(self):
        assert "node.js" in normalize("Node.js")
        assert any("c" in token for token in normalize("C#"))

    def test_single_characters_are_dropped(self):
        assert normalize("a b backend") == ["backend"]
