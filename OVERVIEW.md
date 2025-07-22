# rigX Pipeline Overview

This repository contains a collection of Python modules and Maya scripts that make up the **rigX** pipeline for building and finalizing character rigs.

Key components include:

- `src/rigging_pipeline/` — the core package with utilities for rigging tasks such as dynamic parenting, skin copying, spline rigging, and texture assignment.
- `src/rigging_pipeline/tools/ui/` — PySide2 user interfaces like the Model Toolkit for hierarchy creation, renaming, tagging, and QC checks.
- `shows/` — example show packages (e.g. **Kantara**) with finalize scripts for specific characters.
- `bootstrap.py` — helper to reload the entire pipeline and optionally reload show‑specific modules.

Use `from rigging_pipeline.bootstrap import reload_all; reload_all()` inside Maya to source the pipeline.
