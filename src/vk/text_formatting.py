import re


def format_reply_text(reply_text):
    if not reply_text:
        return ""
    match = re.search(r"\[(?:id|club)\d+\|(?:[^\]]+)], (.*)", reply_text)
    if not match:
        return reply_text if is_valid_text(reply_text) else ""
    text = match.group(1)
    return text if is_valid_text(text) else ""


def format_comment_text(comment_text):
    if not comment_text:
        return ""
    return comment_text if is_valid_text(comment_text) else ""


def is_valid_text(text):
    stripped_text = re.sub(r"[^\u0400-\u04FFa-zA-Z]+", "", text)
    if not stripped_text:
        return False
    return stripped_text.lower() != "спасибо"
