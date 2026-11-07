import pytest

from tatd_bot.vk.text_formatting import (
    format_comment_text,
    format_reply_text,
    is_valid_text,
)


@pytest.mark.parametrize(
    "text",
    [
        "Отличный спектакль",
        "Hello",
        "Спасибо большое",
        "Спектакль 10 из 10!",
    ],
)
def test_valid_text_is_kept(text):
    assert is_valid_text(text)
    assert format_comment_text(text) == text


@pytest.mark.parametrize(
    "text",
    [
        "123 !!",
        "👍",
        "Спасибо!",
        "спасибо",
        "С днём рождения!",
        "С днем рождения",
        "С Днём Рождения, Иван!",
        # намеренно: поздравление отбрасывает весь текст, это спам
        "Поздравляю с днём рождения, спектакль был чудесный",
    ],
)
def test_invalid_text_is_dropped(text):
    assert not is_valid_text(text)
    assert format_comment_text(text) == ""


@pytest.mark.parametrize("text", ["", None])
def test_empty_comment_text(text):
    assert format_comment_text(text) == ""


@pytest.mark.parametrize("text", ["", None])
def test_empty_reply_text(text):
    assert format_reply_text(text) == ""


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("[id123|Иван], отлично", "отлично"),
        ("[club5|Театр], до встречи", "до встречи"),
        ("просто текст", "просто текст"),
    ],
)
def test_reply_mention_is_removed(text, expected):
    assert format_reply_text(text) == expected


@pytest.mark.parametrize(
    "text",
    ["[id123|Иван], спасибо", "[id123|Иван], ", "[id123|Иван], 👍"],
)
def test_reply_without_meaningful_text_is_dropped(text):
    assert format_reply_text(text) == ""


@pytest.mark.parametrize(
    "text",
    ["[id1|И],без пробела", "[id12|Иван] , текст"],
)
def test_reply_mention_in_other_format_is_kept(text):
    assert format_reply_text(text) == text
