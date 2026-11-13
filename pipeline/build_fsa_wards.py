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

import numpy as np
import shapely
from shapely.geometry import shape

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
    project = lambda xy: np.column_stack(t.transform(xy[:, 0], xy[:, 1]))
    return {int(f["properties"]["AREA_SHORT_CODE"]): shapely.transform(shape(f["geometry"]), project).buffer(0)
            for f in g["features"]}


def load_toronto_fsas():
    import shapefile  # pyshp
    from pyproj import CRS
    folder = GEO / "lfsa000b21a_e"          # unzipped download
    zipped = GEO / "lfsa000b21a_e.zip"      # or the zip as downloaded
    if (folder / "lfsa000b21a_e.shp").exists():
        r = shapefile.Reader(str(folder / "lfsa000b21a_e.shp"), encoding="latin-1")
        crs = CRS.from_wkt((folder / "lfsa000b21a_e.prj").read_text())
    elif zipped.exists():
        r = shapefile.Reader(str(zipped), encoding="latin-1")
        crs = CRS.from_wkt(r.prj.read().decode())
    else:
        sys.exit(f"Missing {folder} (or {zipped}). Download the 2021 FSA cartographic boundary file from Statistics Canada.")
    fields = [f[0] for f in r.fields[1:]]
    code_at = fields.index("CFSAUID")
    fsas = {}
    for i, rec in enumerate(r.iterRecords()):
        code = rec[code_at]
        if code.startswith("M"):  # Toronto postal codes all start with M; read only those shapes
            fsas[code] = shape(r.shape(i).__geo_interface__).buffer(0)
    return fsas, crs


def main():
    fsas, crs = load_toronto_fsas()
    table = fsa_wards(fsas, load_wards(crs))
    OUT.write_text(json.dumps(table, indent=0, sort_keys=True), encoding="utf-8")
    multi = sum(1 for v in table.values() if len(v) > 1)
    print(f"{len(table)} postal areas mapped ({multi} cross more than one ward) -> {OUT.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    main()
