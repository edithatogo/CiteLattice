# E09 independent imaging checks

`audit.py` decodes the synthetic scene, Vega-Lite specification and SVG without
calling a production renderer. Every public authority row must have exactly one
scene member. A quantitative value is an exact JSON integer, while a missing or
withheld value remains null. Unsupported layers, tooltips, expressions, external
data URLs and hidden/extra metadata fail the closed fixture profile.

SVG coordinates are checked against exact rational intervals: for value `v`,
maximum public count `m`, and integer bar height `h`, require
`h ≤ 280v/m < h+1` and `y+h=330`. This differs from invoking the writer's integer
division routine. The bar width, spacing, labels, row keys, complete viewBox and
absence of a bar for a null are checked separately. The hand-specified anchors
in `geometry-oracles.json` check these conventions and the >16-row population.

This verifies serialized semantics and the geometry of one synthetic profile.
It does not execute Vega-Lite, rasterize SVG, compile Typst, check screen readers
or contrast, or establish scientific/perceptual benefits. Production
`EvidenceSceneContract` uses a different shape and floating mark values; no
compatibility is inferred. The [output handoff](../outputs/HANDOFF.md) keeps
producer conformance, durable recovery and release admission blocked.
