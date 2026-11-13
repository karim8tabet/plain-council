import hashlib
from bs4 import BeautifulSoup
from .text import normalize

def fingerprint_item(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]): tag.decompose()
    main = soup.find(id="agenda-item-accordion") or soup.find("main") or soup.body or soup
    return hashlib.sha256(normalize(main.get_text(" ", strip=True)).encode()).hexdigest()
