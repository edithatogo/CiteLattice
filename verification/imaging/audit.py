"""Independent scene, Vega-Lite data and exact rational SVG geometry checks.

This is a closed synthetic fixture profile. It does not execute a browser,
Vega renderer, Typst or any production numerical/geometry helper.
"""

from fractions import Fraction

from verification.outputs.audit import (
    MAX_BROWSER_INT, require, read_json, same, xml_document,
)


def _browser_safe(authority):
    require(all(row["publications"] is None or row["publications"] <= MAX_BROWSER_INT
                for row in authority.rows), "browser_precision")


def _scene(authority, data):
    value = read_json(data)
    marks = [{"id": "row:" + row["row_key"], "row_keys": [row["row_key"]],
              "value": row["publications"], "availability": row["availability"],
              "uncertainty": ["source_coverage"]} for row in authority.rows]
    same(value, {"grammar": "e09:synthetic-bars/1.0.0", "metadata": authority.metadata,
                 "marks": marks}, "scene_membership_value_or_disclosure")


def _vega(authority, data):
    same(read_json(data), {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": "E09 synthetic fixture; no producer or renderer qualification",
        "data": {"values": authority.rows}, "mark": "bar",
        "encoding": {"x": {"field": "row_key", "type": "ordinal"},
                     "y": {"field": "publications", "type": "quantitative"}},
        "usermeta": authority.metadata,
    }, "vega_values_lineage_or_hidden_content")


def _svg(authority, data):
    root = xml_document(data)
    ns = "{http://www.w3.org/2000/svg}"
    require(root.tag == ns + "svg", "svg_namespace")
    width = max(640, 80 + 37 * len(authority.rows))
    same(root.attrib, {"viewBox": f"0 0 {width} 400", "role": "img",
                       "aria-label": "E09 synthetic counts"}, "svg_root_attributes")
    require(root.text is None or not root.text.strip(), "svg_hidden_text")
    children = list(root)
    require(len(children) == 3 + len(authority.rows), "svg_membership")
    title, desc, meta = children[:3]
    for node, tag, text in [
        (title, "title", "E09 synthetic counts"),
        (desc, "desc", "Exact accessible values: table.json; missing and withheld counts have no bar."),
    ]:
        require(node.tag == ns + tag and not node.attrib and len(node) == 0 and node.text == text,
                "svg_accessible_description")
    require(meta.tag == ns + "metadata" and not meta.attrib and len(meta) == 0, "svg_metadata")
    same(read_json((meta.text or "").encode()), authority.metadata, "svg_metadata")
    largest = max([row["publications"] for row in authority.rows
                   if row["publications"] is not None] + [1])
    for index, (group, row) in enumerate(zip(children[3:], authority.rows)):
        require(group.tag == ns + "g", "svg_unsupported_element")
        same(group.attrib, {"data-row-key": row["row_key"]}, "svg_row_identity")
        require(group.text is None or not group.text.strip(), "svg_hidden_text")
        observed = row["publications"] is not None
        require(len(group) == (2 if observed else 1), "svg_null_mark")
        x = 30 + 37 * index
        if observed:
            rect = group[0]
            require(rect.tag == ns + "rect" and len(rect) == 0 and not rect.text,
                    "svg_unsupported_element")
            require(set(rect.attrib) == {"x", "y", "width", "height", "fill"}, "svg_active_attributes")
            same({key: rect.attrib[key] for key in ("x", "width", "fill")},
                 {"x": str(x), "width": "26", "fill": "#465f82"}, "svg_geometry")
            height, y = Fraction(rect.attrib["height"]), Fraction(rect.attrib["y"])
            require(height.denominator == y.denominator == 1, "svg_noninteger_geometry")
            # Independent rational inequality, rather than the renderer's floor operation.
            exact = Fraction(row["publications"] * 280, largest)
            require(0 <= height <= exact < height + 1 and y + height == 330, "svg_geometry")
        label = group[-1]
        require(label.tag == ns + "text" and len(label) == 0, "svg_unsupported_element")
        same(label.attrib, {"x": str(x), "y": "350"}, "svg_label_position")
        expected = str(row["publications"]) if observed else row["availability"]
        require(label.text == f'{row["row_key"]}: {expected}', "svg_label_value")
    for node in root.iter():
        require(node.tail is None or not node.tail.strip(), "svg_hidden_text")


def audit_image(authority, kind, data):
    _browser_safe(authority)
    {"scene": _scene, "vega_lite": _vega, "svg": _svg}[kind](authority, data)
