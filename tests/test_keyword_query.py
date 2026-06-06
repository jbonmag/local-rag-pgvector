from app.retrieval.hybrid import _build_or_tsquery


def test_keyword_tsquery_is_or_based_and_deaccented() -> None:
    assert _build_or_tsquery("¿Qué dicen las políticas internas?") == (
        "dicen | politicas | internas"
    )


def test_keyword_tsquery_ignores_short_tokens() -> None:
    assert _build_or_tsquery("el de a") == ""


def test_keyword_tsquery_ignores_common_question_words() -> None:
    assert _build_or_tsquery("¿Cuál es la contraseña privada del administrador?") == (
        "contrasena | privada | administrador"
    )
