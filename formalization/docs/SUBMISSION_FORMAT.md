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
only prepares the entry text (`manifest/declarations.json` has name/module/wikidata for that).
