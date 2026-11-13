from civic.text import normalize, normalize_with_map

def test_normalize():
    assert normalize('trans-\nportation “hello”') == 'transportation "hello"'
    raw = 'A  “quote”'
    normalized, mapping = normalize_with_map(raw)
    assert normalized == 'A "quote"'
    assert raw[mapping[2]:mapping[-1]+1] == '“quote”'
