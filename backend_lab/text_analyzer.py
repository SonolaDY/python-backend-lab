"""Project 1: pure text analysis exposed through JSON."""

import re
from collections import Counter

from flask import Blueprint, abort

from .validation import json_object

bp = Blueprint("text_analyzer", __name__, url_prefix="/api/v1")
# Unicode letters, with internal straight or curly apostrophes; numbers excluded.
WORDS = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)


def analyze(text, top_n):
    words = [word.replace("’", "'").casefold() for word in WORDS.findall(text)]
    counts = Counter(words)
    return {
        "character_count": len(text),
        "word_count": len(words),
        "unique_word_count": len(counts),
        "top_words": [
            {"word": word, "count": count}
            for word, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:top_n]
        ],
    }


@bp.post("/analyze")
def analyze_text():
    data = json_object()
    if set(data) - {"text", "top_n"}:
        abort(400, description="Only text and top_n are supported.")
    text = data.get("text")
    if not isinstance(text, str) or len(text) > 50_000:
        abort(400, description="text must be a string of at most 50,000 characters.")
    top_n = data.get("top_n", 10)
    if type(top_n) is not int or not 1 <= top_n <= 50:
        abort(400, description="top_n must be an integer between 1 and 50.")
    return analyze(text, top_n)
