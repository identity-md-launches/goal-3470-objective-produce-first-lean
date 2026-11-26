/-!
# MissingTheorems

Root of the `MissingTheorems` library. Future proof modules live in
`MissingTheorems/Target01` … `MissingTheorems/Target08`, each with `RouteA` and `RouteB`
subfolders and the disjoint namespaces `MissingTheorems.TargetNN.RouteA` / `….RouteB`.
Submodules are discovered automatically by the `MissingTheorems.+` glob in `lakefile.toml`;
they need not be imported here. This root module intentionally has no proof content.
-/
