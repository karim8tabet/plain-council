"""Build the postal-code-area -> ward lookup used by the website's "Find your ward" box.

Inputs (public boundary files, saved in pipeline/cache/geo/):
  - city-wards-4326.geojson  Toronto Open Data, "City Wards" (25-ward model)
  - lfsa000b21a_e.zip        Statistics Canada, 2021 Census forward sortation areas (FSA)
Output: web/lib/fsa-wards.json  {"M5V": [10], "M6K": [4, 9], ...}

A postal area (first 3 characters of a postal code) can cross ward lines, so the site
asks the resident to pick when there is more than one. Wards covering less than 2% of
an area are dropped: they are slivers where boundary lines don't quite line up.
Overlaps are measured in Statistics Canada's equal-area-ish Lambert projection (metres).
"""
import json
import sys
from pathlib import Path

from shapely.geometry import shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parent
GEO = ROOT / "cache" / "geo"
OUT = ROOT.parent / "web" / "lib" / "fsa-wards.json"
MIN_SHARE = 0.02


def fsa_wards(fsas: dict, wards: dict, min_share: float = MIN_SHARE) -> dict:
    """fsas: {code: polygon}, wards: {number: polygon}, same projected CRS.
    Returns {code: [ward numbers, largest overlap first]} for areas that touch Toronto."""
    out = {}
    for code, poly in sorted(fsas.items()):
        if poly.area == 0:
            continue
        shares = []
        for n, w in wards.items():
            if poly.intersects(w):
                s = poly.intersection(w).area / poly.area
                if s >= min_share:
                    shares.append((s, n))
        if shares:
            out[code] = [n for _, n in sorted(shares, reverse=True)]
    return out


def load_wards(to_crs):
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:4326", to_crs, always_xy=True)
    g = json.loads((GEO / "city-wards-4326.geojson").read_text(encoding="utf-8"))
    return {int(f["properties"]["AREA_SHORT_CODE"]): transform(t.transform, shape(f["geometry"])).buffer(0)
            for f in g["features"]}


def load_toronto_fsas():
    import shapefile  # pyshp
    from pyproj import CRS
    path = GEO / "lfsa000b21a_e.zip"
    if not path.exists():
        sys.exit(f"Missing {path}. Download the 2021 FSA cartographic boundary file (shapefile) from Statistics Canada.")
    r = shapefile.Reader(str(path))
    fields = [f[0] for f in r.fields[1:]]
    crs = CRS.from_wkt(r.prj.read().decode()) if getattr(r, "prj", None) else CRS.from_epsg(3347)
    fsas = {}
    for rec, shp in zip(r.records(), r.shapes()):
        d = dict(zip(fields, rec))
        code = d.get("CFSAUID", "")
        if code.startswith("M"):  # Toronto postal codes all start with M
            fsas[code] = shape(shp.__geo_interface__).buffer(0)
    return fsas, crs


def main():
    fsas, crs = load_toronto_fsas()
    table = fsa_wards(fsas, load_wards(crs))
    OUT.write_text(json.dumps(table, indent=0, sort_keys=True), encoding="utf-8")
    multi = sum(1 for v in table.values() if len(v) > 1)
    print(f"{len(table)} postal areas mapped ({multi} cross more than one ward) -> {OUT.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    main()
