# AntLab — final training and evaluation report

Prepared for an a16z technical review · 7 October 2026 · Independent prototype; no investor affiliation or endorsement.

## 1. Decision in one minute

AntLab works as a browser-based demonstration of ant-colony maze search and stochastic chess move search. Its evolutionary training loop is executable, and the release now has reproducible seeds, a shared website/test engine and raw evidence. It is not a language-model agent platform, a neural network, a strong chess engine, or a demonstrated commercial business.

The final run completed **4 generations, 12 candidate evaluations and 48 training games**, followed by **24 held-out colour-swapped games**, **16 additional greedy-baseline checks**, **40 generated maze trials**, and **19 automated engine tests**. The selected settings were identical to the defaults. Held-out selected-agent points were **12.0/24 (50.0%)**. This release does not demonstrate a training improvement.

The strongest demonstrated asset is an inspectable experiment with reproducible evidence. The investment case still needs an identified user, a costly problem, useful differentiation, and measured adoption. A polished demo does not supply those missing facts.

## 2. What was supplied and what changed

The supplied AntLab.html was a self-contained client-side interface with a remote chess.js dependency, animated mazes, human chess play, an evolutionary settings loop and six-game validation. It referenced earlier offline runs and folders that were not included. Those historical claims were not accepted as evidence for this report.

The release preserves the visual design and algorithm structure while correcting concrete faults: shared engine extraction; locally served chess.js; seeded experimental randomness; frozen settings validation; neutral scoring for drawn chess positions; stop polling even without a progress callback; cancellation that does not play a stopped search's move or save a cancelled training run; run controls that prevent concurrent state corruption; copy fallback; and keyboard/hash navigation. Documentation now identifies material adjudication explicitly. A tested candidate can be loaded from the frozen release file.

The website and offline harness both use engine.js. The offline protocol controls game seeds and records outcomes more rigorously than the small interactive training demonstration. This is not a claim that every browser and Node.js execution has identical timing.

## 3. What the agents actually do

**Maze agent.** A randomized depth-first generator produces a connected grid maze and opens extra passages. Each ant follows neighbouring cells using pheromone strength and a Manhattan-distance hint. It avoids immediately returning to the previous cell when another option exists. Successful routes have loops erased, add pheromone, and compete for the shortest discovered route. Pheromone evaporates between rounds. Breadth-first search supplies an exact shortest-path baseline on this unweighted graph.

**Chess agent.** Candidate legal moves come from chess.js. Before sampled lines run, the engine checks immediate opponent captures, promotions and mate-in-one replies. Each ant samples a first move using pheromone and a heuristic, then explores a short line. The evaluation is material plus a small centre-control bonus. Better-scoring rollouts reinforce move pheromone. The final choice combines sampled values with the root heuristic. Those scores are not calibrated win probabilities.

**Training.** Five settings change: pheromone exponent a, heuristic exponent b, evaporation rho, rollout depth D and move sampling T. Each generation evaluates the current incumbent and two mutations. The candidate with the highest training score survives; exact ties retain the incumbent. No weights, representations, language model, persistent task memory or online learning system are trained. Pheromone is reset for each chess search, so it does not become long-term learning across games.

Ant-colony optimization is established prior art, not an AntLab invention. The original Ant System paper describes cooperating agents and positive-feedback search. [Original paper, Dorigo, Maniezzo and Colorni (1996)](https://iridia.ulb.ac.be/~mdorigo/Published_papers/All_Dorigo_papers/DorManCol1996tsmcb.pdf).

## 4. Frozen protocol and separation of evidence

| Stage | Protocol |
|---|---|
| Training | 4 generations × 3 candidates × 4 games; 16 ants per move; 30 half-move cap |
| Candidate mutation | Base seed 20261007; generation-specific mutation seed |
| Training match seeds | 31000–31003 reused across candidates; alternate colours |
| Selection | Highest mean points; ties keep earlier incumbent; no held-out scores used |
| Held-out test | 12 seed pairs, 91000–91011; two games per seed with colours swapped; 16 ants per move; 30 half-move cap |
| Extra baseline check | Default and selected agent each play 8 games against greedy, seeds 101000–101007 |
| Mazes | 10 independent seeds at each size 10, 15, 20, 28; 25 ants × 40 rounds; cap 3×size² steps per ant |
| Tactical checks | Three constructed mate-in-one positions plus one stalemate; not a representative puzzle dataset |
| Unit/regression checks | 19 tests using the same engine file |

Each game is recorded with its seed, colours, PGN, final FEN, plies, evaluation and termination reason. Checkmate supplies actual game points, rules draws supply 0.5, and unfinished games are **adjudicated** after 30 half-moves: white receives 1 if evaluation exceeds +200, 0 below −200, otherwise 0.5. Thus a training score of 1.00 does not mean every game ended in checkmate. The benchmark starts from the standard chess position; it does not test opening diversity, long games or human play.

## 5. Final training results

| Generation | Candidate | Points per game vs greedy |
|---|---|---|
| 1 | 1 | 1.00 |
| 1 | 2 | 1.00 |
| 1 | 3 | 1.00 |
| 2 | 1 | 1.00 |
| 2 | 2 | 1.00 |
| 2 | 3 | 1.00 |
| 3 | 1 | 1.00 |
| 3 | 2 | 1.00 |
| 3 | 3 | 1.00 |
| 4 | 1 | 1.00 |
| 4 | 2 | 1.00 |
| 4 | 3 | 1.00 |

Frozen selected settings: `a=1, b=3, rho=0.08, D=4, T=3`.

All training candidates tied at 1.00. The incumbent survived every tie, so the final candidate is the original default configuration. The experiment completed successfully, but its fitness function supplied no useful discrimination. Calling that a learned stronger policy would be false.

## 6. Held-out chess results and uncertainty

| Measure | Observed result |
|---|---|
| Selected-agent points | 12.0/24 |
| Points per game | 0.500 |
| Points-based W / neutral / L (includes adjudication) | 9 / 6 / 9 |
| Actual checkmates | 2 |
| Rules draws | 0 |
| Material-adjudicated endings | 22 |
| Paired bootstrap, conditional 95% interval | 0.500–0.500 |
| Constructed tactical cases passed | 4/4 |

The bootstrap resamples the 12 observed colour-swapped pairs 10,000 times with seed 441. It is conditional on this engine, fixed opening, short-game adjudication rule and observed samples. Because the two configurations are identical and each pair swaps roles using the same seed, a narrow or degenerate interval is a symmetry artifact. It does not demonstrate precise playing strength or a robust learned policy. This small test cannot establish commercial performance, broad chess competence, or generalization to real-world agent tasks.

Additional held-out greedy checks:

| Agent | Adjudicated points |
|---|---|
| default | 8.0/8 |
| selected | 8.0/8 |

These checks show how the baseline behaves on a separate seed set. They do not rescue an uninformative training objective. The release has not been tested against Stockfish, a depth-controlled minimax engine or a representative tactical suite. Established engine testing uses dedicated game-testing infrastructure; see [Stockfish's Fishtest project](https://github.com/official-stockfish/fishtest). No comparison result against that system is claimed.

## 7. Maze results

| Size | Solved | Exact-optimal | Mean extra steps, solved only | Mean ants reaching goal | BFS ms | Ant search ms |
|---|---|---|---|---|---|---|
| 10×10 | 10/10 | 10/10 | 0.00% | 99.9% | 0.443 | 90.6 |
| 15×15 | 10/10 | 9/10 | 0.42% | 99.7% | 0.094 | 122.0 |
| 20×20 | 10/10 | 9/10 | 0.23% | 99.4% | 0.214 | 253.0 |
| 28×28 | 10/10 | 7/10 | 1.19% | 99.5% | 0.224 | 448.5 |

Every discovered route was checked for legal neighbouring cells, start/goal endpoints, and length at least as long as the exact BFS route. Extra-step means exclude unsolved trials; the solved column must be read beside them. Reach rate counts successful walks among 1,000 ants, not the percentage of mazes solved. All mazes belong to one connected generated distribution; no weighted graphs, disconnected graphs, changing obstacles or routing constraints were tested.

Timing is a single local Node.js run on this Windows machine, measured around each algorithm. It excludes browser drawing and is sensitive to scheduling and hardware. Ants receive a much larger compute budget than BFS. These timings do not establish a scalable performance advantage; in unweighted static mazes, BFS is already exact. A useful ant-search advantage would need to appear on a task where exact methods become costly or the objective changes—not be inferred from this visualization.

## 8. What works, what does not, and what remains unverified

| Capability | Status | Evidence or practical limit |
|---|---|---|
| Connected maze generation and BFS baseline | Works in tested sizes/seeds | Legal-path assertions and 40 maze trials |
| Pheromone search | Works within the tested simulation | Solved/optimal counts above; no optimality guarantee |
| Legal chess search and board-state restoration | Works in tests | Search leaves its input game unchanged; selected moves legal |
| Immediate mate and draw handling | Works in constructed cases | Three mate positions and stalemate; no broad tactical guarantee |
| Evolutionary training execution | Works | 48 recorded training games; settings frozen before held-out evaluation |
| Training improvement | Not demonstrated | Flat fitness and held-out evidence above |
| Independent held-out seeds and colour balance | Implemented | 24 recorded games in 12 paired seeds |
| Honest outcome labels | Corrected | Material adjudication separated from rules endings |
| Stop/reset/state controls | Corrected implementation | Stop polling regression and browser interaction checks; no exhaustive race proof |
| Saved candidate loading | Implemented | Numeric bounds validated before applying stored parameters |
| Copy CSV | Implemented with fallback | Clipboard can be denied; manual text selection remains available |
| Large-scale concurrent computation | Missing | Main-thread chess work; single active experiment, no worker farm |
| Strong chess ability or Elo | Unverified | No external engine, human match or rated evaluation |
| Neural/LLM agent training | Not implemented | Search-setting optimization only |
| Multi-task autonomous software agents | Not implemented | No tool use, planning workflow, integrations or persistent task memory |
| Shared accounts, hosted training jobs, collaboration | Missing | Static client app; local browser persistence only |
| Customer demand, retention, revenue, paid pilots | Unverified | No customer evidence supplied or collected |
| Cross-browser and broad accessibility coverage | Partial | Focused in-app browser checks; not a complete Chrome/Safari/mobile matrix |

## 9. Automated test receipts

| Test | Result |
|---|---|
| Maze generation reproduces the same seed | Pass |
| Different seeds produce different maze layouts | Pass |
| BFS route is connected and legal at every size | Pass |
| Loop erasure preserves a simple connected path | Pass |
| Pheromones stay positive and finite | Pass |
| Ant paths do not cross walls or beat exact BFS | Pass |
| Search returns a legal move without mutating the input game | Pass |
| Chess search reproduces a fixed seed | Pass |
| White mate-in-one is detected | Pass |
| Black mate-in-one is detected | Pass |
| Stalemate is neutral and no move is returned | Pass |
| Insufficient-material draw is neutral | Pass |
| Mutations are bounded across 1,000 samples | Pass |
| Corrupt persisted settings are rejected | Pass |
| Stop is polled without a progress callback | Pass |
| Stopped game returns no outcome | Pass |
| Chess rules library accepts a legal castling move | Pass |
| Chess rules library enforces en passant | Pass |
| Chess rules library supports queen promotion | Pass |

Passing software tests establish the checked behavior, not algorithm superiority. They do not substitute for independent evaluation datasets, usability research or product demand. Raw test names and execution times are in tests.json. Source hashes and runtime version are in results.json.

Browser checks confirmed maze solving, a three-maze comparison and clipboard copy; manual chess moves/undo; a mate puzzle; training start/cancel with restored controls; candidate loading; hash restoration; and an automatic black reply. Browser automation did not reliably dispatch the chess-stop click before a search finished, so that UI timing case remains unverified. Engine stop polling passed its regression test. Clipboard-denied and storage-denied fallbacks are implemented but were not forced in this browser. The final training/validation protocol ran offline through the same engine; the complete interactive loop was not replayed as a second full evaluation. See browser-qa.json.

## 10. Investor-facing positioning

The accurate pitch is: **“AntLab makes stochastic search experiments visible and reproducible. It compares swarm heuristics with exact baselines, records what the algorithms do, and exposes when a training objective fails.”** That is a defensible account of the current prototype. “Self-improving frontier agents,” “beats classical algorithms,” “strong chess AI” and “proven training gain” are unsupported.

The plausible first customer hypothesis is an instructor or developer who wants a hands-on way to teach and debug search algorithms. A second, much larger hypothesis is a reproducible experiment workspace for optimization teams. Neither has been validated. Educational engagement does not automatically imply research-team purchasing demand. General LLM-agent infrastructure is outside the demonstrated scope.

The algorithm itself is established and straightforward to copy. Current potential differentiation is the clarity of the experiment workflow and the quality of its evidence, which still need user validation. No defensible data advantage, distribution advantage, switching cost, proprietary model or recurring revenue has been demonstrated. Market size, price, users and traction are deliberately not invented.

For an a16z discussion, present this as an engineering prototype and a testable product hypothesis. The useful ask is introductions to technical educators or optimization practitioners for structured design-partner exercises. A claim to venture-scale readiness would require substantially more evidence.

## 11. Prioritized next experiments and decisions

1. Replace the saturated greedy fitness with a depth-controlled opponent and diverse fixed openings. Use equal computation budgets. Freeze candidate selection and evaluate on untouched seeds/openings. Report rules endings separately from adjudication, and avoid repeated tuning on the held-out set.
2. Run ablations: no pheromone reinforcement, no distance/root heuristic, and matched-budget random rollout. The current run does not isolate whether pheromone is doing useful work or the hand-designed heuristic supplies most of the result.
3. For chess, add a representative tactical corpus and longer games before any strength claim. For mazes, add weighted or dynamic routing only if a concrete user needs it; compare against appropriate exact/heuristic baselines with a documented budget.
4. Move long-running computation into a worker and make checkpoints/export robust. Add replay/import of experiment seeds and a versioned result format before team use.
5. Conduct three instructor/developer walkthroughs. Observe whether users can predict, debug and explain failures better than with an ordinary notebook. Measure completion and time, not just compliments. No target is presented as already achieved.
6. Decide the product direction from evidence. If users only want a classroom visualization, build for that. If a costly research workflow emerges, test a narrowly scoped paid pilot. If neither signal appears, retain AntLab as a portfolio project instead of inflating its business claims.

## 12. Reproduction and evidence package

Serve this folder over HTTP to run the website. Node.js is needed only for offline tests and experiments; there is no npm install step. chess.js is bundled at the same version the supplied HTML used.

```
node test.cjs
node experiment.cjs
```

The second command regenerates training, held-out games, maze trials, tests-independent experiment evidence and frozen candidate settings. It overwrites results.json and trained-settings.json; preserve the release snapshot before starting new experiments. Numerical seeded behavior is intended to reproduce with the same engine and dependency, while timings are expected to vary.

Files: index.html (app), engine.js (shared search), chess.min.js and chess-LICENSE.txt (rules/dependency), experiment.cjs (protocol), test.cjs (regressions), results.json (full game/maze records and hashes), tests.json (test receipt), trained-settings.json (frozen settings), maze-results.csv (trial table), README.md (run instructions), report.html and REPORT.md (this report).

Experiment runtime: v24.19.0. Recorded start: 2026-10-07T09:21:23.362Z; finish: 2026-10-07T10:12:57.663Z (UTC). Source SHA-256 values are included in the raw protocol. This is the final evaluation for this release, not a certification that future versions need no further testing.
