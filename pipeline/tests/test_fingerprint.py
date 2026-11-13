from pathlib import Path
from civic.fingerprint import fingerprint_item

def test_fingerprint_stable_and_content_sensitive():
    html = (Path(__file__).parent/'fixtures'/'item_2026.EX31.2.html').read_text(encoding='utf8')
    assert fingerprint_item(html) == fingerprint_item(html)
    changed = html.replace('maximum heat bylaw', 'changed heat bylaw', 1)
    assert fingerprint_item(html) != fingerprint_item(changed)
