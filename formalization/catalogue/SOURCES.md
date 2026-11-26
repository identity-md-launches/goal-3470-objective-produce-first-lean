# Catalogue sources (fetched 2026-11-26)
* https://leanprover-community.github.io/1000-missing.html -> `1000-missing.html` (SHA256 1a9af1ba0294155a31dbad45ebb8fbf9f098514dba854aa4b1f81fecf5c23e95, equals the pinned 1a9af1ba…c23e95: MATCH). HTTP headers: `missing.headers`.
* https://leanprover-community.github.io/1000.html -> `1000.html` (SHA256 1371fc89783b7419046a20a3da05013003df983d4a67d080c4923150664ca6c5); headers `1000.headers`.
* `mathlib-pinned/`: `docs/1000.yaml`, `scripts/yaml_check.py`, `docs/workflows.md` from Mathlib fc4f59e5.
* `missing-entries.json|tsv`: all 956 entries, ids exactly as displayed (incl. 18 suffixed: Q…A/B/X), titles unescaped; no canonical-Q guessing. Regenerate: `python3 -I catalogue/extract.py`.
* `drift.json`: 956 entries, 956 distinct ids (945 distinct base Q numbers because of suffixes); every missing-page id is present in the pinned yaml, none has a `decl`; 1 has only `statement` (Fermat's Last Theorem, Q132469); 25 yaml ids have neither decl nor statement yet are absent from the missing page (page/yaml drift, listed). The page text says "Among these, 1 have their statement formalized", consistent.
