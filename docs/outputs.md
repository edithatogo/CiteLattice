# Typed scientific output chain — implementation and limits

This incremental adapter writes Parquet, XLSX and Typst report source from the same immutable `PublicationSummary.annual` table that powers the existing CSV, SVG, HTML and RO-Crate slice.

Parquet uses Arrow Int32 year and UInt64 publication counts, with schema metadata recording source input hash and CiteLattice result schema; workbook stores exact numeric counts within Excel's safe integer precision and strings otherwise. Typst source is generated from numeric data, with no remote dependencies or raw untrusted titles.

**Typst source is not itself PDF**. A PDF is only claimed when an authorised, pinned Typst renderer compiles it and the output is independently checked for integrity, accessibility and rights. Workbook/PDF format support is separate from scientific method validity.

Maintain a single authoritative source table and independent artifact digests. Avoid silent row truncation and count conversion to inaccurate floating-point values. Validation must include native reading of Parquet and workbook content, not only file existence.

## Transactional publication (increment under review)

`write_extended_transactional` stages the existing Parquet/XLSX/Typst outputs in a temporary directory under the final destination's parent, verifies each artifact SHA-256, rewrites the final manifest path, and publishes by a single same-filesystem directory rename. The destination must not exist and the parent must already exist. Denied exports create no package; staging is cleaned up on failure.

This prevents consumers from seeing an incomplete package through the designated final path under normal single-writer operation. It is **not** a guarantee against a concurrent external writer replacing the destination, abrupt-power-loss durability, malicious filesystem mutation or remote object-store semantics. A future durable mode must fsync files/directories, implement exclusive no-replace publication, and verify package signatures and disclosure controls. The direct `write_extended` API remains non-transactional for compatibility.

The transactional API writes the **portable relative manifest path** inside its package, while the returned in-process receipt points to the caller's final destination. This prevents absolute local filesystem paths from affecting package bytes or leaking the caller's directory layout.
