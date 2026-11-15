"""Read-only E09 fixture-profile auditor, independent of production writers.

The authority is supplied separately from the candidate bundle. Digests establish
byte identity only: every supported artifact is also decoded and compared with
the authority. This deliberately narrow profile is not a production wire schema,
a general document sanitizer, or a release-qualification decision.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
from html.parser import HTMLParser
import importlib.metadata
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile


PROFILE = "org.citelattice.e09.synthetic-source/1.0.0"
AUDIT_VERSION = "1.0.0"
MAX_BYTES = 8 * 1024 * 1024
MAX_EXPANDED_BYTES = 16 * 1024 * 1024
MAX_ROWS = 512
MAX_U64 = 2**64 - 1
MAX_BROWSER_INT = 2**53 - 1
READER_PINS = {"pyarrow": "19.0.1", "openpyxl": "3.1.5",
               "et-xmlfile": "2.0.0", "defusedxml": "0.7.1"}
COLUMNS = [
    {"name": "row_key", "type": "utf8", "nullable": False, "unit": "identifier"},
    {"name": "year", "type": "int32", "nullable": True, "unit": "calendar_year"},
    {"name": "publications", "type": "uint64", "nullable": True, "unit": "works"},
    {"name": "availability", "type": "utf8", "nullable": False, "unit": "category"},
    {"name": "label", "type": "utf8", "nullable": False, "unit": "text"},
    {"name": "rights", "type": "utf8", "nullable": False, "unit": "category"},
]
NAMES = [column["name"] for column in COLUMNS]
FORMATS = {
    "disclosure.json": "disclosure", "table.json": "json", "table.csv": "csv",
    "table.arrow": "arrow_ipc", "table.parquet": "parquet", "table.xlsx": "xlsx",
    "table.html": "html", "table.typ": "typst_source",
}
IMAGE_FORMATS = {"scene.json": "scene", "chart.vl.json": "vega_lite", "chart.svg": "svg"}


class AuditError(ValueError):
    """Fixed error codes deliberately exclude paths, cells and source payloads."""


def require(condition, code):
    if not condition:
        raise AuditError(code)


def canonical(value):
    """Local fixture encoding, NOT RFC 8785 or a production identity algorithm."""
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("ascii")


def same(actual, expected, code="semantic_mismatch"):
    # Python's ordinary equality equates True, 1 and 1.0. This comparison does not.
    require(canonical(actual) == canonical(expected), code)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate_json_key")
        result[key] = value
    return result


def _constant(_value):
    raise AuditError("nonfinite_json")


def read_json(data):
    require(len(data) <= MAX_BYTES, "byte_budget")
    return json.loads(data, object_pairs_hook=_pairs, parse_constant=_constant)


def xml_document(data):
    """UTF-8, no DTD/entities/processing instructions/comments, bounded bytes."""
    require(len(data) <= MAX_BYTES, "byte_budget")
    text = data.decode("utf-8")
    text = re.sub(r'^<\?xml\s[^?]*\?>', '', text, count=1)
    require("<!" not in text and "<?" not in text, "active_xml")
    return ET.fromstring(text)


def require_reader(name):
    try:
        version = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        raise AuditError("reader_unavailable") from None
    require(version == READER_PINS[name], "reader_version_mismatch")


@dataclass(frozen=True)
class Authority:
    """Only repository-authored, independently supplied synthetic authorities."""

    fixture_id: str
    rows: list[dict]
    metadata: dict
    forbidden_tokens: tuple[str, ...]
    imaging: bool


def _authority(data):
    value = read_json(data)
    same(sorted(value), sorted([
        "profile", "fixture_version", "origin", "license", "policy", "id", "rows",
        "expected", "imaging",
    ]), "source_shape")
    require(value["profile"] == PROFILE and value["fixture_version"] == "1.0.0",
            "source_version")
    require(value["license"] == "CC0-1.0" and type(value["origin"]) is str,
            "source_provenance")
    require(type(value["id"]) is str and re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", value["id"]),
            "source_identity")
    policy = value["policy"]
    same(sorted(policy), ["disclose_withheld_count", "export_allowed", "id", "version"],
         "rights_shape")
    require(policy["export_allowed"] is True, "export_denied")
    require(type(policy["disclose_withheld_count"]) is bool and
            policy["id"] == "e09:synthetic-rights" and policy["version"] == "1.0.0",
            "rights_version")
    require(type(value["imaging"]) is bool, "source_shape")
    rows = value["rows"]
    require(type(rows) is list and len(rows) <= MAX_ROWS, "row_budget")
    keys, public, forbidden = set(), [], []
    for row in rows:
        same(sorted(row), sorted(NAMES), "source_row_shape")
        for name in ("row_key", "availability", "label", "rights"):
            require(type(row[name]) is str and len(row[name]) <= 256, "source_string")
        require(re.fullmatch(r"[A-Za-z0-9_-]{1,64}", row["row_key"]), "source_row_key")
        require(row["row_key"] not in keys, "duplicate_source_row")
        keys.add(row["row_key"])
        require(row["year"] is None or (type(row["year"]) is int and
                -(2**31) <= row["year"] < 2**31), "source_year")
        require(row["publications"] is None or (type(row["publications"]) is int and
                0 <= row["publications"] <= MAX_U64), "source_count")
        require(row["availability"] in ("observed", "missing", "withheld"), "source_null_state")
        require((row["availability"] == "observed") == (row["publications"] is not None),
                "source_null_state")
        require(row["rights"] in ("public", "withhold"), "unknown_rights")
        if row["rights"] == "public":
            public.append(row)
        else:
            # Whole-row denial. Neither row identity nor label belongs in any artifact.
            forbidden.extend((row["row_key"], row["label"]))
    counts = {
        "source_rows": len(rows), "exported_rows": len(public),
        "withheld_rows": len(rows) - len(public),
        "missing_counts": sum(row["availability"] == "missing" for row in public),
        "withheld_counts": sum(row["availability"] == "withheld" for row in public),
        "undated_rows": sum(row["year"] is None for row in public),
        "known_publications": str(sum(row["publications"] for row in public
                                      if row["publications"] is not None)),
    }
    same(counts, value["expected"], "independent_known_answer_mismatch")
    if not policy["disclose_withheld_count"]:
        # A source total would also reveal the excluded row count by subtraction.
        counts["source_rows"] = counts["withheld_rows"] = None
    if value["imaging"]:
        require(all(row["publications"] is None or row["publications"] <= MAX_BROWSER_INT
                    for row in public), "browser_precision")
    metadata = {
        "profile": PROFILE, "source_sha256": sha256(data),
        "projection_sha256": sha256(canonical(public)), "columns": COLUMNS,
        "rights_policy": policy, "counts": counts,
        "null_policy": "null/NULL/blank with explicit availability; never zero-fill",
        "csv_policy": "apostrophe-prefix text starting with = + - @ tab CR LF or apostrophe",
        "xlsx_policy": "uint64 above u32::MAX is decimal text; nullable numbers are blank",
    }
    return Authority(value["id"], public, metadata, tuple(forbidden), value["imaging"])


def _redacted(call, *args):
    try:
        return call(*args)
    except AuditError:
        raise
    except Exception:
        # Third-party parsers often include cell contents or filenames in exceptions.
        raise AuditError("malformed_artifact") from None


def authority_from_bytes(data):
    return _redacted(_authority, data)


def load_authority(path):
    return _redacted(lambda: authority_from_bytes(_read_file(Path(path))))


def _read_file(path):
    require(not path.is_symlink() and path.is_file(), "nonregular_artifact")
    require(path.stat().st_size <= MAX_BYTES, "byte_budget")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    require(len(data) <= MAX_BYTES, "byte_budget")
    return data


def text_rows(authority):
    return [["NULL" if row[name] is None else str(row[name]) for name in NAMES]
            for row in authority.rows]


def _check_tokens(authority, text):
    require(all(not token or token not in text for token in authority.forbidden_tokens),
            "restricted_payload")


def _csv(authority, data):
    rows = list(csv.reader(io.StringIO(data.decode("utf-8"), newline=""), strict=True))
    expected = [NAMES]
    for original, cells in zip(authority.rows, text_rows(authority)):
        for i, name in enumerate(NAMES):
            if type(original[name]) is str and cells[i].startswith(tuple("=+-@\t\r\n'")):
                cells[i] = "'" + cells[i]
        expected.append(cells)
    same(rows, expected, "csv_semantics_or_formula")


class _HTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.cells, self.rows, self.headers, self.meta = [], [], [], [], []
        self.current = ""
        self.tags = []

    def handle_starttag(self, tag, attrs):
        require(len(attrs) == len(dict(attrs)), "html_duplicate_attribute")
        attrs = dict(attrs)
        parents = {"html": None, "head": "html", "meta": "head", "title": "head",
                   "body": "html", "h1": "body", "table": "body", "thead": "table",
                   "tbody": "table", "tr": ("thead", "tbody"), "th": "tr", "td": "tr"}
        require(tag in parents, "active_or_hidden_html")
        parent = self.stack[-1] if self.stack else None
        allowed = parents[tag]
        require(parent in allowed if type(allowed) is tuple else parent == allowed,
                "html_structure")
        if tag == "html":
            same(attrs, {"lang": "en"}, "html_attributes")
        elif tag == "meta":
            if attrs == {"charset": "utf-8"}:
                self.meta.append("charset")
            else:
                require(set(attrs) == {"name", "content"} and attrs["name"] == "e09",
                        "html_metadata")
                self.meta.append(read_json(attrs["content"].encode()))
        else:
            same(attrs, {}, "html_attributes")
        self.tags.append(tag)
        if tag != "meta":
            self.stack.append(tag)
        if tag in ("th", "td", "title", "h1"):
            self.current = ""
        if tag == "tr":
            self.cells = []

    def handle_startendtag(self, tag, attrs):
        require(tag == "meta", "html_structure")
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        require(self.stack and self.stack[-1] == tag, "html_structure")
        if tag in ("th", "td"):
            require(self.stack[-3] == ("thead" if tag == "th" else "tbody"), "html_structure")
            self.cells.append(self.current)
        elif tag in ("title", "h1"):
            require(self.current == "E09 synthetic table", "html_text")
        elif tag == "tr":
            if self.stack[-2] == "thead":
                self.headers.append(self.cells)
            else:
                self.rows.append(self.cells)
        self.stack.pop()

    def handle_data(self, data):
        if self.stack and self.stack[-1] in ("th", "td", "title", "h1"):
            self.current += data
        else:
            require(not data.strip(), "html_hidden_text")

    def handle_comment(self, _data):
        raise AuditError("html_comment")

    def handle_decl(self, _data):
        raise AuditError("html_declaration")

    def handle_pi(self, _data):
        raise AuditError("html_processing_instruction")


def _html(authority, data):
    parser = _HTML()
    parser.feed(data.decode("utf-8"))
    parser.close()
    require(not parser.stack, "html_structure")
    for tag in ("html", "head", "title", "body", "h1", "table", "thead", "tbody"):
        require(parser.tags.count(tag) == 1, "html_structure")
    same(parser.meta, ["charset", authority.metadata], "html_metadata")
    same(parser.headers, [NAMES], "html_headers")
    same(parser.rows, text_rows(authority), "html_rows")


def _typst(authority, data):
    # Read a closed, literal #text table grammar. Do not evaluate Typst code.
    source = data.decode("utf-8")
    first, body = source.split("\n", 1)
    prefix = "#let e09_metadata = "
    require(first.startswith(prefix), "typst_metadata")
    metadata = read_json(read_json(first[len(prefix):].encode()).encode())
    same(metadata, authority.metadata, "typst_metadata")
    require(body.startswith("#table(columns: 6,\n") and body.endswith(")\n"),
            "typst_literal_grammar")
    body = body[len("#table(columns: 6,\n"):-2]
    token = re.compile(r'\s*\[#text\(("(?:[^"\\\x00-\x1f]|\\.)*")\)\],\s*')
    cells, position = [], 0
    while position < len(body):
        match = token.match(body, position)
        require(match is not None, "typst_active_expression")
        cells.append(read_json(match.group(1).encode()))
        position = match.end()
    same(cells, NAMES + [cell for row in text_rows(authority) for cell in row], "typst_rows")


def _arrow_schema(authority, pa):
    types = {"utf8": pa.string(), "int32": pa.int32(), "uint64": pa.uint64()}
    fields = [pa.field(c["name"], types[c["type"]], nullable=c["nullable"],
                       metadata={b"unit": c["unit"].encode()}) for c in COLUMNS]
    return pa.schema(fields, metadata={b"e09": canonical(authority.metadata)})


def _arrow(authority, data, parquet):
    require_reader("pyarrow")
    import pyarrow as pa
    import pyarrow.ipc as ipc
    import pyarrow.parquet as pq

    source = pa.BufferReader(data)
    if parquet:
        reader = pq.ParquetFile(source, thrift_string_size_limit=MAX_BYTES,
                                thrift_container_size_limit=10000)
        require(reader.metadata.num_rows == len(authority.rows) and
                reader.metadata.num_columns == len(NAMES) and
                reader.metadata.num_row_groups <= 128, "parquet_shape")
        require(sum(reader.metadata.row_group(i).total_byte_size
                    for i in range(reader.metadata.num_row_groups)) <= MAX_EXPANDED_BYTES,
                "expanded_byte_budget")
        require(set(reader.metadata.metadata or {}) == {b"e09", b"ARROW:schema"},
                "parquet_hidden_metadata")
        require(reader.metadata.created_by == "parquet-cpp-arrow version 19.0.1",
                "parquet_writer_metadata")
        table = reader.read(use_threads=False)
    else:
        reader = ipc.open_file(source)
        require(reader.num_record_batches <= 128, "arrow_batch_budget")
        batches = []
        for index in range(reader.num_record_batches):
            item = reader.get_batch_with_custom_metadata(index)
            require(item.custom_metadata is None, "arrow_hidden_batch_metadata")
            batches.append(item.batch)
        table = pa.Table.from_batches(batches, schema=reader.schema)
    require(table.schema.equals(_arrow_schema(authority, pa), check_metadata=True),
            "arrow_types_nullability_units_metadata")
    require(table.num_rows == len(authority.rows) and table.nbytes <= MAX_EXPANDED_BYTES,
            "arrow_shape")
    same(table.to_pylist(), authority.rows, "arrow_values")


_XLSX_MEMBERS = {
    "[Content_Types].xml", "_rels/.rels", "docProps/app.xml", "docProps/core.xml",
    "xl/workbook.xml", "xl/_rels/workbook.xml.rels", "xl/styles.xml",
    "xl/theme/theme1.xml", "xl/sharedStrings.xml",
    "xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml",
}


def _xlsx_preflight(authority, data):
    require(data.startswith(b"PK\x03\x04") and data[-22:-18] == b"PK\x05\x06",
            "xlsx_prefix_or_trailing_payload")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        info = archive.infolist()
        names = [item.filename for item in info]
        require(not archive.comment and all(not item.comment and not item.extra for item in info),
                "xlsx_zip_hidden_metadata")
        require(len(names) == len(set(names)) and len(names) <= len(_XLSX_MEMBERS),
                "xlsx_duplicate_or_extra_part")
        require(set(names) <= _XLSX_MEMBERS, "xlsx_unsupported_part")
        require(sum(item.file_size for item in info) <= MAX_EXPANDED_BYTES, "expanded_byte_budget")
        for item in info:
            require(item.file_size <= MAX_BYTES and not item.is_dir(), "xlsx_part_budget")
            raw = archive.read(item)
            root = xml_document(raw)
            _check_tokens(authority, raw.decode("utf-8"))
            _check_tokens(authority, "".join(root.itertext()))
            for element in root.iter():
                local = element.tag.rsplit("}", 1)[-1]
                require(local not in {
                    "f", "hyperlink", "definedName", "externalReference", "oleObject",
                    "extLst", "dataValidation", "conditionalFormatting", "drawing",
                    "legacyDrawing", "picture", "pivotTable", "sheetProtection",
                }, "xlsx_formula_or_unsupported_content")
                require(element.attrib.get("TargetMode") != "External", "xlsx_external_link")
                require(element.attrib.get("state") not in ("hidden", "veryHidden") and
                        element.attrib.get("hidden", "0") in ("0", "false"), "xlsx_hidden_content")
                for text in element.attrib.values():
                    _check_tokens(authority, text)
        _xlsx_closed_parts(authority, archive)


def _xlsx_closed_parts(authority, archive):
    """Constrain surfaces that a cell reader intentionally ignores.

    Static fixture encoding parts are allowlisted by digest. The mutable cell
    area is fully enumerated, including unused strings and ignored XML nodes.
    This is deliberately stricter than general XLSX file compatibility.
    """
    profile = read_json(_read_file(Path(__file__).with_name("xlsx-profile.json")))
    for name, digest in profile["static_parts_sha256"].items():
        require(sha256(archive.read(name)) == digest, "xlsx_static_disclosure_surface")
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    raw_strings = archive.read("xl/sharedStrings.xml")
    require(len(re.findall(rb'\sxmlns(?::[A-Za-z0-9_-]+)?=', raw_strings)) == 1,
            "xlsx_namespace_payload")
    sst = xml_document(raw_strings)
    require(sst.tag == ns + "sst" and set(sst.attrib) == {"count", "uniqueCount"}, "xlsx_strings")
    strings = []
    for item in sst:
        require(item.tag == ns + "si" and not item.attrib and len(item) == 1,
                "xlsx_rich_or_hidden_strings")
        text = item[0]
        require(text.tag == ns + "t" and len(text) == 0 and
                text.attrib in ({}, {"{http://www.w3.org/XML/1998/namespace}space": "preserve"}),
                "xlsx_rich_or_hidden_strings")
        strings.append(text.text or "")
    require(len(set(strings)) == len(strings) and sst.attrib["uniqueCount"] == str(len(strings)),
            "xlsx_unused_or_duplicate_strings")
    data_rows = [NAMES]
    for row in authority.rows:
        data_rows.append([str(row[name]) if name == "publications" and row[name] is not None
                          and row[name] > 2**32 - 1 else row[name] for name in NAMES])
    meta_rows = [[key, canonical(value).decode()] for key, value in sorted(authority.metadata.items())]
    used = []
    for number, rows in enumerate((data_rows, meta_rows), 1):
        name = f"xl/worksheets/sheet{number}.xml"
        raw = archive.read(name)
        shell = re.sub(rb'<dimension ref="[^"]+"/>', b'<dimension ref="DYNAMIC"/>', raw, count=1)
        shell = re.sub(rb'<sheetData>.*?</sheetData>', b'<sheetData/>', shell, count=1, flags=re.S)
        require(sha256(shell) == profile["worksheet_shells_sha256"][name],
                "xlsx_worksheet_disclosure_surface")
        inner = re.search(rb'<sheetData>(.*?)</sheetData>', raw, flags=re.S)
        require(inner is not None and b"xmlns" not in inner.group(1), "xlsx_namespace_payload")
        root = xml_document(raw)
        dimension = root.find(ns + "dimension")
        width = len(rows[0])
        same(dimension.attrib, {"ref": f"A1:{chr(64+width)}{len(rows)}"}, "xlsx_dimensions")
        sheet = root.find(ns + "sheetData")
        require(len(sheet) == len(rows) and not sheet.attrib, "xlsx_physical_rows")
        for i, (element, expected) in enumerate(zip(sheet, rows), 1):
            require(element.tag == ns + "row", "xlsx_ignored_xml")
            same(element.attrib, {"r": str(i), "spans": f"1:{width}"}, "xlsx_physical_row")
            populated = [(j, value) for j, value in enumerate(expected) if value is not None]
            require(len(element) == len(populated), "xlsx_physical_cells")
            for cell, (j, value) in zip(element, populated):
                require(cell.tag == ns + "c" and len(cell) == 1 and cell[0].tag == ns + "v" and
                        not cell[0].attrib and len(cell[0]) == 0, "xlsx_physical_cell")
                attributes = {"r": f"{chr(65+j)}{i}"}
                if type(value) is str:
                    attributes["t"] = "s"
                    raw_index = cell[0].text or ""
                    require(re.fullmatch(r"0|[1-9][0-9]*", raw_index), "xlsx_string_reference")
                    index = int(raw_index)
                    require(0 <= index < len(strings), "xlsx_string_reference")
                    used.append(index)
                    require(strings[index] == value, "xlsx_string_value")
                else:
                    require(cell[0].text == str(value), "xlsx_exact_numeric_cell")
                same(cell.attrib, attributes, "xlsx_physical_type")
        for node in sheet.iter():
            require(node.tail is None or not node.tail.strip(), "xlsx_hidden_xml_text")
            if node.tag != ns + "v":
                require(node.text is None or not node.text.strip(), "xlsx_hidden_xml_text")
    require(set(used) == set(range(len(strings))) and sst.attrib["count"] == str(len(used)),
            "xlsx_unused_or_duplicate_strings")
    for node in sst.iter():
        require(node.tail is None or not node.tail.strip(), "xlsx_hidden_xml_text")
        if node.tag != ns + "t":
            require(node.text is None or not node.text.strip(), "xlsx_hidden_xml_text")


def _xlsx(authority, data):
    for name in ("openpyxl", "et-xmlfile", "defusedxml"):
        require_reader(name)
    _xlsx_preflight(authority, data)
    import openpyxl

    workbook = openpyxl.load_workbook(io.BytesIO(data), data_only=False,
                                     read_only=False, keep_links=True)
    try:
        same(workbook.sheetnames, ["Data", "Disclosure"], "xlsx_sheets")
        require(not workbook.defined_names and not workbook._external_links, "xlsx_external_link")
        for sheet in workbook:
            require(sheet.sheet_state == "visible", "xlsx_hidden_content")
            require(not sheet._charts and not sheet._images and not sheet._pivots, "xlsx_extra_content")
            require(sheet.max_row <= MAX_ROWS + 20 and sheet.max_column <= len(NAMES), "xlsx_shape")
            for row in sheet:
                for cell in row:
                    require(cell.data_type != "f" and cell.comment is None and cell.hyperlink is None,
                            "xlsx_formula_or_extra_content")
        sheet = workbook["Data"]
        require(sheet.max_row == len(authority.rows) + 1 and sheet.max_column == len(NAMES), "xlsx_shape")
        same([cell.value for cell in sheet[1]], NAMES, "xlsx_headers")
        for i, row in enumerate(authority.rows, 2):
            for j, name in enumerate(NAMES, 1):
                cell, expected = sheet.cell(i, j), row[name]
                if name == "publications" and expected is not None and expected > 2**32 - 1:
                    expected = str(expected)
                same(cell.value, expected, "xlsx_value_or_precision")
                if type(expected) is str:
                    require(cell.data_type in ("s", "inlineStr"), "xlsx_text_type")
                else:
                    require(cell.data_type == "n", "xlsx_number_type")
        metadata_rows = [[key, canonical(value).decode()] for key, value in sorted(authority.metadata.items())]
        meta = workbook["Disclosure"]
        require(meta.max_column == 2 and meta.max_row == len(metadata_rows), "xlsx_metadata_shape")
        same([[cell.value for cell in row] for row in meta], metadata_rows, "xlsx_metadata")
        require(all(cell.data_type in ("s", "inlineStr") for row in meta for cell in row),
                "xlsx_metadata_type")
    finally:
        workbook.close()


def _artifact(authority, kind, data):
    require(type(data) is bytes and len(data) <= MAX_BYTES, "byte_budget")
    if kind in ("json", "disclosure"):
        expected = authority.metadata if kind == "disclosure" else {
            "metadata": authority.metadata, "rows": authority.rows}
        same(read_json(data), expected)
    elif kind == "csv":
        _csv(authority, data)
    elif kind == "html":
        _html(authority, data)
    elif kind == "typst_source":
        _typst(authority, data)
    elif kind in ("arrow_ipc", "parquet"):
        _arrow(authority, data, kind == "parquet")
    elif kind == "xlsx":
        _xlsx(authority, data)
    elif kind in IMAGE_FORMATS.values():
        from verification.imaging.audit import audit_image
        audit_image(authority, kind, data)
    else:
        raise AuditError("unsupported_format")


def audit_artifact(authority, kind, data):
    """Decode a single fixture-profile artifact; any unknown content fails closed."""
    return _redacted(_artifact, authority, kind, data)


def required_artifacts(authority):
    return FORMATS | (IMAGE_FORMATS if authority.imaging else {})


def _bundle(authority, root):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), "bundle_directory")
    expected = required_artifacts(authority)
    require({entry.name for entry in root.iterdir()} == set(expected) | {"manifest.json"},
            "bundle_missing_or_unlisted_asset")
    manifest = read_json(_read_file(root / "manifest.json"))
    same(sorted(manifest), ["artifacts", "profile", "source_sha256"], "manifest_shape")
    require(manifest["profile"] == PROFILE, "manifest_version")
    require(manifest["source_sha256"] == authority.metadata["source_sha256"], "manifest_source")
    items = manifest["artifacts"]
    require(type(items) is list and len(items) == len(expected), "manifest_membership")
    seen, results = set(), []
    for item in items:
        same(sorted(item), ["format", "path", "sha256"], "manifest_shape")
        name = item["path"]
        require(type(name) is str and name in expected and name not in seen and
                PurePosixPath(name).name == name, "manifest_membership")
        seen.add(name)
        require(item["format"] == expected[name], "manifest_format")
        data = _read_file(root / name)
        require(sha256(data) == item["sha256"], "artifact_digest")
        audit_artifact(authority, item["format"], data)
        results.append({"path": name, "format": item["format"], "sha256": sha256(data), "status": "passed"})
    return {
        "auditor_version": AUDIT_VERSION, "fixture_id": authority.fixture_id,
        "source_sha256": authority.metadata["source_sha256"], "status": "passed",
        "claim": "synthetic-fixture-auditor-only", "release_qualified": False,
        "blocked_prerequisites": ["E04", "pinned-producer-conformance", "durable-spool-recovery"],
        "reader_versions": {name: importlib.metadata.version(name) for name in READER_PINS},
        "artifacts": sorted(results, key=lambda item: item["path"]),
    }


def audit_bundle(authority, root):
    """Require every profile artifact; missing readers are failures, never passes."""
    return _redacted(_bundle, authority, root)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("authority", type=Path)
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit_bundle(load_authority(args.authority), args.bundle)
    except AuditError as error:
        print(json.dumps({"status": "failed", "code": str(error), "release_qualified": False}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
