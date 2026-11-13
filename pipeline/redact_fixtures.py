"""Remove the names of people who wrote in or spoke from saved City item pages (test data).

The City publishes these names, but Plain Council never shows or stores them (counts only),
so our repository shouldn't republish them either. Each distinct name becomes
"[name removed #N]" (the same person keeps the same number), so the tests still count
submissions and speakers exactly as the real page would.

Usage: python redact_fixtures.py <file.html> [...]   (edits the files in place)
"""
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

_ENTRY = re.compile(r"^(\s*\((?:January|February|March|April|May|June|July|August|September|October|November|December)"
                    r" \d{1,2}, \d{4}\)\s*[\w-]+(?:\s+\w+)?\s+from)\s+(.+?)(\s*\([A-Z]{2}\.[\w.]+\))?\s*$", re.S)


def redact(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    ids: dict[str, int] = {}

    def tag(name: str) -> str:
        key = " ".join(name.split()).lower()
        ids.setdefault(key, len(ids) + 1)
        return f"[name removed #{ids[key]}]"

    for h in soup.find_all("h4"):
        heading = h.get_text(" ", strip=True)
        section = h.find_next_sibling()
        if section is None:
            continue
        if heading.startswith("Communications"):
            for span in section.find_all("span"):
                m = _ENTRY.match(span.get_text())
                if m:
                    span.string = f" {m.group(1)} {tag(m.group(2))}{m.group(3) or ''} "
        elif heading == "Speakers":
            for node in list(section.descendants):
                if isinstance(node, NavigableString) and node.strip():
                    node.replace_with(f"\n{tag(node.strip())} ")
    return str(soup)


if __name__ == "__main__":
    for f in sys.argv[1:]:
        p = Path(f)
        p.write_text(redact(p.read_text(encoding="utf-8")), encoding="utf-8")
        print("redacted", f)
