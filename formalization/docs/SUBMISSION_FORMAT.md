# 1000+ theorems database: actual submission format (read from pinned Mathlib; nothing submitted)

Source: `catalogue/mathlib-pinned/1000.yaml` (Mathlib `fc4f59e5…`, `docs/1000.yaml`) and the schema in
`catalogue/mathlib-pinned/yaml_check.py` (dataclass `ThousandPlusTheorem`, checked by `scripts/yaml_check.py`).

Top level is a mapping `WIKIDATA_ID -> entry`. Keys: `Q` + digits, optionally one disambiguating letter
suffix (`Q4724004A`, `…X`); the suffix is part of the key. Entry fields (all optional except `title`):

* `title` (str, required) – human readable title; e.g. `title: Schwenk's theorem`.
* `decl` (str) – name of the Mathlib/Archive/Counterexamples declaration that proves the theorem.
* `decls` (list of str) – like `decl` when split over several declarations (never both: error).
* `statement` (str) – declaration that only *states* the theorem (no proof).
* `authors` (str), `date` (`YYYY`, `YYYY-MM` or `YYYY-MM-DD`), `url` (external project), `comment` (str).
  Unknown keys make `yaml_check.py` fail (`TypeError`). Declaration names are checked to exist (check-yaml.lean).

Example (existing): `Q26708: {title: Binomial theorem, decl: add_pow, authors: Chris Hughes}`.
Entries without `decl` are the "missing" ones (the missing page lists them). Entries live in Mathlib's
`docs/1000.yaml`, so an entry is added by a Mathlib PR after the declaration is merged upstream; this project
only prepares the entry text (local route manifests record name/module/wikidata; see below).

## Local verification manifest and evidence

The local JSON manifest is separate from the upstream YAML database entry. Each independent worker
places a tracked manifest at `reports/TargetNN/RouteA/declarations.json` or `RouteB/declarations.json`:

```json
{
  "declarations": [
    {
      "name": "MissingTheorems.TargetNN.RouteA.theorem_name",
      "module": "MissingTheorems.TargetNN.RouteA.Result",
      "wikidata": "the target's actual Wikidata ID",
      "target": "TargetNN",
      "route": "RouteA"
    }
  ]
}
```

This is a schema illustration, not a theorem submission. Replace all illustrative values with the
actual declaration, module and target identity. `name` and `module` are required. The harness checks
that the source file exists and that Lean's environment identifies that module as the declaration's
defining module. Route manifests must name modules under their own target and route. Optional `target`
and `route` fields, when present, must agree with the manifest location. Dotted ordinary identifiers
are supported; quoted Lean identifiers are not. Names must be unique across the aggregate manifest
set; several declarations may legitimately share one module. JSON duplicate keys are rejected.

For one route, use `scripts/axioms.sh --runtime DIR --manifest reports/TargetNN/RouteA/declarations.json`.
Add `--module MissingTheorems.TargetNN.RouteA.Result` to build just one module and its project imports;
all selected manifest entries must then name that module. Full checks automatically discover route
manifests and also retain nonempty legacy entries in `manifest/declarations.json`. Stage new files
first: snapshots use current tracked sources, not untracked files or existing build output. No shared
registry or root import edit is required.

Empty proof manifests are errors. `--infrastructure-only` is the sole explicit empty mode, and records
that no proof was verified. The harness permits only `propext`, `Classical.choice`, and `Quot.sound`,
and rejects missing names and unrecognized `#print axioms` output. Its token scan is not a complete
kernel audit. A build/axiom pass is not a theorem-fidelity or novelty claim.

Retain exact commands and exit codes, the toolchain and Mathlib pins, runtime manifest digest and
provenance, build log, original axiom output, and an honest description of network isolation. Identify
whether the test used a supplemental runtime or only committed files. Dead proxies alone must be
reported **UNVERIFIED**, never as a network-isolation pass. Also supply the theorem's plain-English
statement and proof, fidelity review, prior-work check, and ready upstream YAML entry. Mark every
unperformed review **UNVERIFIED**. Infrastructure evidence lives in `reports/infrastructure/`; theorem
routes should keep evidence in their own report directory so workers do not edit shared files.
