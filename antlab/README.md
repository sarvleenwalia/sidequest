# AntLab

Browser-based ant-colony search experiments, with reproducible final evaluation.

Live: https://sarvleenwalia.github.io/sidequest/antlab/

Read [the final report](report.html) or [REPORT.md](REPORT.md). This release does not demonstrate training improvement or strong chess ability.

Serve this directory over HTTP for the browser UI. Offline: `node test.cjs` then `node experiment.cjs`. These use the same engine as the site. The experiment command regenerates result files.

The final protocol includes 48 training games, 24 held-out games, 16 extra greedy checks, 40 maze trials and 19 engine tests. Search-setting evolution is not neural/LLM training. Short unfinished games are explicitly material-adjudicated.

chess.js 0.10.3 is bundled under BSD-2-Clause; see chess-LICENSE.txt. No proprietary rights over that dependency or the established ant-colony algorithm are claimed.
