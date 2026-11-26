#!/usr/bin/env python3 -I
"""Extract the 956 entries of 1000-missing.html (ids verbatim, no canonical-Q guessing) and
compare with the pinned Mathlib docs/1000.yaml. Run: python3 -I catalogue/extract.py"""
import hashlib, html, json, os, re
D = os.path.dirname(os.path.abspath(__file__))
raw = open(os.path.join(D, "1000-missing.html"), encoding="utf-8").read()
entries = []
for m in re.finditer(r'<p><a href="https://www\.wikidata\.org/wiki/([^"]+)">([^<]*?):</a>\s*(.*?)</p>', raw, re.S):
    href_id, shown, title = m.group(1), m.group(2), html.unescape(re.sub(r"<[^>]+>", "", m.group(3))).strip()
    entries.append({"id": shown, "href_id": href_id, "title": title,
                    "suffix": (re.fullmatch(r"Q\d+([A-Za-z]*)", shown) or [None, None])[1] or ""})
ids = [e["id"] for e in entries]
yaml_txt = open(os.path.join(D, "mathlib-pinned", "1000.yaml"), encoding="utf-8").read()
ydecl, ytop = {}, []
cur = None
for line in yaml_txt.split("\n"):
    m = re.match(r"^(Q\w+):\s*$", line)
    if m: cur = m.group(1); ytop.append(cur); continue
    m = re.match(r"^  (decls?|statement):\s*(.*)$", line)
    if m and cur: ydecl.setdefault(cur, []).append(m.group(1))
base = lambda i: re.sub(r"[A-Za-z]+$", "", i)
drift = {
  "entry_count": len(entries), "suffixed_ids": sorted(i for i in ids if i != base(i)),
  "suffixed_count": sum(1 for i in ids if i != base(i)),
  "duplicate_ids": sorted({i for i in ids if ids.count(i) > 1}),
  "distinct_ids": len(set(ids)), "distinct_base_q_numbers": len({base(i) for i in ids}),
  "href_differs_from_shown": [e for e in entries if e["href_id"] != e["id"]],
  "pinned_yaml_entries": len(ytop), "pinned_yaml_with_decl_or_statement": len(ydecl),
  "missing_page_ids_absent_from_pinned_yaml": sorted(set(ids) - set(ytop)),
  "missing_page_ids_with_decl_in_pinned_yaml": sorted(i for i in ids if i in ydecl and "statement" != ydecl[i][0] or (i in ydecl and "decl" in ydecl[i])),
  "missing_page_ids_with_statement_only_in_pinned_yaml": sorted(i for i in ids if i in ydecl and set(ydecl[i]) == {"statement"}),
  "yaml_ids_without_decl_not_on_missing_page": sorted(set(ytop) - set(ydecl) - set(ids)),
  "missing_page_sha256": hashlib.sha256(raw.encode()).hexdigest(),
}
json.dump(entries, open(os.path.join(D, "missing-entries.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(D, "missing-entries.tsv"), "w", encoding="utf-8").write("id\ttitle\n" + "".join(f"{e['id']}\t{e['title']}\n" for e in entries))
json.dump(drift, open(os.path.join(D, "drift.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in drift.items()}, indent=1))
