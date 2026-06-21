"""工具函数测试"""

from src.utils.text import (
    truncate,
    extract_key_sentences,
    count_characters,
    safe_json_parse,
)


class TestTruncate:
    def test_short_text(self):
        assert truncate("你好", max_length=10) == "你好"

    def test_long_text_sentence_boundary(self):
        text = "第一句。第二句。第三句。第四句。"
        result = truncate(text, max_length=8)
        assert len(result) <= 11  # "第一句。" + "..." = 7
        assert result.endswith("。...") or result.endswith("...")

    def test_long_text_no_sentence_boundary(self):
        text = "a" * 100
        result = truncate(text, max_length=50)
        assert len(result) == 53  # 50 + "..."
        assert result.endswith("...")


class TestExtractKeySentences:
    def test_extract_sentences(self):
        text = "今天天气真好。适合出去走走。你觉得呢？"
        sentences = extract_key_sentences(text, max_sentences=2)
        assert len(sentences) == 2
        assert "今天天气真好" in sentences

    def test_english_punctuation(self):
        text = "Hello world. This is a test. Goodbye!"
        sentences = extract_key_sentences(text, max_sentences=2)
        assert len(sentences) >= 1

    def test_short_sentences_filtered(self):
        text = "好。行。可以。这是一个较长的句子。"
        sentences = extract_key_sentences(text)
        # "好" "行" "可以" 长度 <= 5 被过滤
        assert all(len(s) > 5 for s in sentences)


class TestCountCharacters:
    def test_chinese_count(self):
        stats = count_characters("你好世界")
        assert stats["chinese"] == 4

    def test_mixed_text(self):
        stats = count_characters("Hello 你好 123！")
        assert stats["chinese"] == 2
        assert stats["english"] == 5  # Hello
        assert stats["digits"] == 3
        assert stats["total"] == 13

    def test_empty_string(self):
        stats = count_characters("")
        assert stats["total"] == 0


class TestSafeJsonParse:
    def test_plain_json(self):
        result = safe_json_parse('{"name": "test", "value": 123}')
        assert result is not None
        assert result["name"] == "test"
        assert result["value"] == 123

    def test_markdown_wrapped(self):
        text = """```json
{"key": "value"}
```"""
        result = safe_json_parse(text)
        assert result is not None
        assert result["key"] == "value"

    def test_trailing_comma(self):
        result = safe_json_parse('{"items": [1, 2, 3,]}')
        assert result is not None
        assert result["items"] == [1, 2, 3]

    def test_invalid_json(self):
        result = safe_json_parse("这不是 JSON")
        assert result is None

    def test_comment_removal(self):
        result = safe_json_parse('{"name": "test" // 这是注释\n}')
        assert result is not None
        assert result["name"] == "test"
