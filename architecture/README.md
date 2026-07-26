# Architecture Diagrams

The system architecture, warehouse data model, and KPI metric tree are
documented as ASCII diagrams directly in the main [README.md](../README.md)
(Architecture and Warehouse Model sections) and in the mart/staging SQL
comments in `sql/`, rather than as separate static image exports —
this keeps them versioned as text and reviewable in pull-request diffs.

If you'd like rendered PNG/SVG versions for a slide deck or a wiki page,
the ASCII diagrams in the README translate directly into a diagramming
tool (Excalidraw, Lucidchart, dbt docs' auto-generated DAG view if you
adopt dbt per the "Future enhancements" section) — the node/edge structure
is already fully specified there.
