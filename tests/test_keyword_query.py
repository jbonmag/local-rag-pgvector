from app.retrieval.hybrid import _build_or_tsquery


def test_keyword_tsquery_is_or_based_and_deaccented() -> None:
    assert _build_or_tsquery("What do the internal policies say?") == "internal | policies"


def test_keyword_tsquery_ignores_short_tokens() -> None:
    assert _build_or_tsquery("to an a") == ""


def test_keyword_tsquery_ignores_common_question_words() -> None:
    assert _build_or_tsquery("What is the private administrator password?") == (
        "private | administrator | password"
    )
