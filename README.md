# Sidequest

A project discovery studio for curious students across computing, STEM, humanities, and design. Working name; not affiliated with MIT.

## Run

Open `index.html` in a browser, or run `node server.mjs` and visit the printed local address. No dependencies or build step.

## Current website

- Six disciplines and fifteen curated project structures.
- Experience and time constraints adjust project scope.
- Optional interest lens, alternate ideas, source lineage, and downloadable Markdown briefs.
- Responsive layout and accessible native controls.
- A feature-detected browser agent action uses the same generator as the interface.

The current generator is curated and deterministic apart from initial selection. It does **not** call an AI model, retrieve new papers, certify novelty, or produce unlimited unique projects. The interest lens is framing, not a semantic project rewrite.

See [the concept](CONCEPT.md), [research](RESEARCH.md), and [generator specification](GENERATOR.md).

## Next implementation

Add a server-side model integration and verified source retrieval. Keep credentials off the client. Validate structured model outputs against discipline-specific project criteria before displaying them. Distinguish checked source facts from generated proposals.
