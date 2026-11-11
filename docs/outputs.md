# Typed scientific output chain — implementation and limits

This incremental adapter writes Parquet, XLSX and Typst report source from the same immutable `PublicationSummary.annual` table that powers the existing CSV, SVG, HTML and RO-Crate slice.

Parquet uses Arrow Int32 year and UInt64 publication counts, with schema metadata recording source input hash and CiteLattice result schema; workbook stores exact numeric counts within Excel's safe integer precision and strings otherwise. Typst source is generated from numeric data, with no remote dependencies or raw untrusted titles.

**Typst source is not itself PDF**. A PDF is only claimed when an authorised, pinned Typst renderer compiles it and the output is independently checked for integrity, accessibility and rights. Workbook/PDF format support is separate from scientific method validity.

Maintain a single authoritative source table and independent artifact digests. Avoid silent row truncation and count conversion to inaccurate floating-point values. Validation must include native reading of Parquet and workbook content, not only file existence.
