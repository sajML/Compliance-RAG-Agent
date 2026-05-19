from app.services.retriever import _tokenize


class TestTokenize:
    def test_basic_tokenization(self):
        assert _tokenize("Hello World") == ["hello", "world"]

    def test_strips_punctuation(self):
        tokens = _tokenize("GDPR, Article 5(1)(a).")
        assert "gdpr" in tokens
        assert "article" in tokens
        assert "5" in tokens
        assert "1" in tokens
        assert "a" in tokens

    def test_empty_string(self):
        assert _tokenize("") == []

    def test_lowercases(self):
        assert _tokenize("DATA PROTECTION") == ["data", "protection"]
