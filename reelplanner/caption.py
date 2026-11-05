"""Simple caption checks before a reel goes out."""

import re

MAX_CAPTION = 2200          # Instagram's hard limit
PREVIEW_CHARS = 125         # roughly what shows before "... more"
MAX_HASHTAGS = 5

HASHTAG_RE = re.compile(r"#\w+")


def hashtags(text: str) -> list[str]:
    return HASHTAG_RE.findall(text)


def check(text: str) -> list[str]:
    """Return a list of problems. Empty list means the caption looks fine."""
    problems = []
    if not text.strip():
        return ["caption is empty"]
    if len(text) > MAX_CAPTION:
        problems.append(f"too long: {len(text)} characters (limit {MAX_CAPTION})")
    first_line = text.strip().splitlines()[0]
    if len(first_line) > PREVIEW_CHARS:
        problems.append(
            f"first line is {len(first_line)} characters - it gets cut at about {PREVIEW_CHARS}"
        )
    tags = hashtags(text)
    if len(tags) > MAX_HASHTAGS:
        problems.append(f"{len(tags)} hashtags - keep it to {MAX_HASHTAGS} or fewer")
    dupes = {t.lower() for t in tags if [x.lower() for x in tags].count(t.lower()) > 1}
    if dupes:
        problems.append(f"repeated hashtags: {', '.join(sorted(dupes))}")
    if "—" in text:
        problems.append("contains an em dash (reads as AI-written)")
    return problems
