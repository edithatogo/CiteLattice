"""Encode synthetic known answers for testing the independent auditor.

No production code or auditor helpers are imported. Regeneration is opt-in and
requires a new destination. These files are harness inputs, not producer output.
"""

import argparse
from datetime import datetime
import csv
import hashlib
import html
import importlib.metadata
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def dump(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build(source_path, destination):
    for name, pin in (("pyarrow", "19.0.1"), ("XlsxWriter", "3.2.9")):
        if importlib.metadata.version(name) != pin:
            raise RuntimeError("fixture writer version mismatch")
    import pyarrow as pa
    import pyarrow.ipc as ipc
    import pyarrow.parquet as pq
    import xlsxwriter

    raw = source_path.read_bytes()
    source = json.loads(raw)
    if (source["profile"] != "org.citelattice.e09.synthetic-source/1.0.0"
            or source["license"] != "CC0-1.0" or source["policy"]["export_allowed"] is not True):
        raise ValueError("fixture source not authorised")
    rows = [row for row in source["rows"] if row["rights"] == "public"]
    if source["imaging"] and any(row["publications"] is not None and
                                  row["publications"] > 9007199254740991 for row in rows):
        raise ValueError("fixture counts exceed the browser precision limit")
    names = ["row_key", "year", "publications", "availability", "label", "rights"]
    columns = [
        {"name": "row_key", "type": "utf8", "nullable": False, "unit": "identifier"},
        {"name": "year", "type": "int32", "nullable": True, "unit": "calendar_year"},
        {"name": "publications", "type": "uint64", "nullable": True, "unit": "works"},
        {"name": "availability", "type": "utf8", "nullable": False, "unit": "category"},
        {"name": "label", "type": "utf8", "nullable": False, "unit": "text"},
        {"name": "rights", "type": "utf8", "nullable": False, "unit": "category"},
    ]
    counts = dict(source["expected"])
    if not source["policy"]["disclose_withheld_count"]:
        counts["source_rows"] = counts["withheld_rows"] = None
    meta = {
        "profile": source["profile"], "source_sha256": digest(raw),
        "projection_sha256": digest(dump(rows).encode()), "columns": columns,
        "rights_policy": source["policy"], "counts": counts,
        "null_policy": "null/NULL/blank with explicit availability; never zero-fill",
        "csv_policy": "apostrophe-prefix text starting with = + - @ tab CR LF or apostrophe",
        "xlsx_policy": "uint64 above u32::MAX is decimal text; nullable numbers are blank",
    }
    destination.mkdir(parents=True, exist_ok=False)
    assets = {}

    def text(name, kind, value):
        (destination / name).write_text(value, encoding="utf-8", newline="\n")
        assets[name] = kind

    text("table.json", "json", dump({"metadata": meta, "rows": rows}) + "\n")
    text("disclosure.json", "disclosure", dump(meta) + "\n")
    cells = [["NULL" if row[name] is None else str(row[name]) for name in names] for row in rows]
    with (destination / "table.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(names)
        for row, values in zip(rows, cells):
            writer.writerow([("'" + value) if isinstance(row[name], str) and value and
                             value[0] in "=+-@\t\r\n'" else value
                             for name, value in zip(names, values)])
    assets["table.csv"] = "csv"
    types = {"utf8": pa.string(), "int32": pa.int32(), "uint64": pa.uint64()}
    schema = pa.schema([pa.field(c["name"], types[c["type"]], nullable=c["nullable"],
                                metadata={b"unit": c["unit"].encode()}) for c in columns],
                       metadata={b"e09": dump(meta).encode()})
    table = pa.Table.from_pylist(rows, schema=schema)
    with pa.OSFile(str(destination / "table.arrow"), "wb") as stream:
        with ipc.new_file(stream, schema) as writer:
            writer.write_table(table)
    assets["table.arrow"] = "arrow_ipc"
    pq.write_table(table, destination / "table.parquet", version="2.6", compression="NONE",
                   use_dictionary=False, write_statistics=True)
    assets["table.parquet"] = "parquet"
    with xlsxwriter.Workbook(destination / "table.xlsx", {
        "strings_to_formulas": False, "strings_to_urls": False,
    }) as book:
        book.set_properties({"created": datetime(2026, 1, 1)})
        sheet = book.add_worksheet("Data")
        for j, name in enumerate(names):
            sheet.write_string(0, j, name)
        for i, row in enumerate(rows, 1):
            for j, name in enumerate(names):
                value = row[name]
                if value is None:
                    sheet.write_blank(i, j, None)
                elif isinstance(value, str) or (name == "publications" and value > 4294967295):
                    sheet.write_string(i, j, str(value))
                else:
                    sheet.write_number(i, j, value)
        disclosure = book.add_worksheet("Disclosure")
        for i, (name, value) in enumerate(sorted(meta.items())):
            disclosure.write_string(i, 0, name)
            disclosure.write_string(i, 1, dump(value))
    assets["table.xlsx"] = "xlsx"
    html_source = (
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="e09" content="' + html.escape(dump(meta), quote=True) + '">'
        '<title>E09 synthetic table</title></head><body><h1>E09 synthetic table</h1>'
        '<table><thead><tr>' + ''.join('<th>' + name + '</th>' for name in names) +
        '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + html.escape(v) + '</td>'
        for v in row) + '</tr>' for row in cells) + '</tbody></table></body></html>\n'
    )
    text("table.html", "html", html_source)
    typst = '#let e09_metadata = ' + dump(dump(meta)) + '\n#table(columns: 6,\n'
    typst += ''.join('  [#text(' + dump(cell) + ')],\n' for row in [names] + cells for cell in row)
    text("table.typ", "typst_source", typst + ')\n')
    if source["imaging"]:
        scene = {"grammar": "e09:synthetic-bars/1.0.0", "metadata": meta,
                 "marks": [{"id": "row:" + row["row_key"], "row_keys": [row["row_key"]],
                            "value": row["publications"], "availability": row["availability"],
                            "uncertainty": ["source_coverage"]} for row in rows]}
        text("scene.json", "scene", dump(scene) + "\n")
        vega = {"$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "description": "E09 synthetic fixture; no producer or renderer qualification",
                "data": {"values": rows}, "mark": "bar",
                "encoding": {"x": {"field": "row_key", "type": "ordinal"},
                             "y": {"field": "publications", "type": "quantitative"}},
                "usermeta": meta}
        text("chart.vl.json", "vega_lite", dump(vega) + "\n")
        largest = max([row["publications"] for row in rows if row["publications"] is not None] + [1])
        svg = ET.Element("svg", {"xmlns": "http://www.w3.org/2000/svg",
                                 "viewBox": f"0 0 {max(640, 80 + len(rows)*37)} 400",
                                 "role": "img", "aria-label": "E09 synthetic counts"})
        ET.SubElement(svg, "title").text = "E09 synthetic counts"
        ET.SubElement(svg, "desc").text = "Exact accessible values: table.json; missing and withheld counts have no bar."
        ET.SubElement(svg, "metadata").text = dump(meta)
        for i, row in enumerate(rows):
            group = ET.SubElement(svg, "g", {"data-row-key": row["row_key"]})
            x = 30 + i * 37
            if row["publications"] is not None:
                height = row["publications"] * 280 // largest
                ET.SubElement(group, "rect", {"x": str(x), "y": str(330-height), "width": "26",
                                              "height": str(height), "fill": "#465f82"})
            label = str(row["publications"]) if row["publications"] is not None else row["availability"]
            ET.SubElement(group, "text", {"x": str(x), "y": "350"}).text = row["row_key"] + ": " + label
        text("chart.svg", "svg", ET.tostring(svg, encoding="unicode") + "\n")
    manifest = {"profile": source["profile"], "source_sha256": digest(raw), "artifacts": [
        {"path": name, "format": kind, "sha256": digest((destination / name).read_bytes())}
        for name, kind in sorted(assets.items())]}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("authority", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    build(args.authority, args.destination)
