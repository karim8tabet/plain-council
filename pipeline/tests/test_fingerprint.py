from pathlib import Path
from civic.fingerprint import fingerprint_item

def test_fingerprint_stable_and_content_sensitive():
    html = (Path(__file__).parent/'fixtures'/'item_2026.EX31.2.html').read_text(encoding='utf8')
    assert fingerprint_item(html) == fingerprint_item(html)
    changed = html.replace('maximum heat bylaw', 'changed heat bylaw', 1)
    assert fingerprint_item(html) != fingerprint_item(changed)


def test_recheck_marks_only_changed_pages():
    from recheck import changed_items
    pages = {"A": "<main>Council adopted the item.</main>", "B": "<main>Council adopted the item as amended.</main>"}
    stored = fingerprint_item("<main>Council adopted the item.</main>")

    def fetch(ref):
        if ref == "C":
            raise ConnectionError("site down")
        return pages[ref]

    items = [{"ref": r, "source_fingerprint": stored} for r in ("A", "B", "C")]
    assert changed_items(items, fetch) == [("A", False), ("B", True), ("C", None)]
