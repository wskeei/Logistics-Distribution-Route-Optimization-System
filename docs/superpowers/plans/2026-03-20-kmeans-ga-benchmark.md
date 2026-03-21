# KMeans+GA Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a publication-ready benchmark pipeline to evaluate the two-stage `KMeans+GA` multi-vehicle route planning algorithm with quality-time tradeoff evidence.

**Architecture:** Use a dual-layer benchmark design. Layer A runs large-scale reproducible experiments with an offline Haversine matrix. Layer B runs small sampled validation with ORS road-network matrices. Compare `Random/Nearest`, `GA-only`, `OR-Tools CVRP`, and `KMeans+GA` under unified constraints and budgets.

**Tech Stack:** Python 3.10+, FastAPI project backend, OR-Tools, NumPy/Pandas, SciPy/Statsmodels (or Pingouin), Matplotlib/Seaborn, pytest.

---

## 1. File Structure Map

### New files
- `backend/benchmark/README.md`: Benchmark usage, experiment protocol, and reproducibility notes.
- `backend/benchmark/config.py`: Global benchmark constants (seeds, scales, time limits, budgets).
- `backend/benchmark/types.py`: Shared dataclasses/pydantic for instances and results.
- `backend/benchmark/generate_instances.py`: Deterministic synthetic instance generator.
- `backend/benchmark/distance.py`: Haversine matrix and ORS matrix abstraction.
- `backend/benchmark/algorithms/random_nearest.py`: Weak baseline.
- `backend/benchmark/algorithms/ga_only.py`: Global GA baseline without KMeans.
- `backend/benchmark/algorithms/ortools_cvrp.py`: Strong baseline wrapper.
- `backend/benchmark/algorithms/kmeans_ga.py`: Main method implementation.
- `backend/benchmark/runner.py`: Single-run execution and raw result logging.
- `backend/benchmark/run_suite.py`: Full experiment orchestration.
- `backend/benchmark/analyze.py`: Statistical summary and significance tests.
- `backend/benchmark/plot.py`: Plot generation for paper figures.
- `backend/tests/test_benchmark_generator.py`: Reproducibility and schema tests.
- `backend/tests/test_benchmark_feasibility.py`: Capacity and feasibility checks.
- `backend/tests/test_benchmark_runner.py`: End-to-end smoke test for one instance.
- `docs/superpowers/specs/2026-03-20-kmeans-ga-benchmark-design.md`: Approved design spec snapshot used by implementers.
- `docs/benchmark-methodology.md`: Paper-facing experiment methodology section.

### Modified files
- `backend/pyproject.toml`: Add benchmark dependencies and entrypoints.
- `backend/seed_data.py`: Add optional deterministic mode and shared generation utilities (if reused).
- `README.md`: Add benchmark section and reproduction commands.

### Output directories (generated)
- `backend/benchmark/datasets/instances/`
- `backend/benchmark/results/raw/`
- `backend/benchmark/results/summary/`
- `backend/benchmark/plots/`

---

### Task 1: Benchmark scaffold and dependency setup

**Files:**
- Create: `backend/benchmark/README.md`
- Create: `backend/benchmark/config.py`
- Create: `backend/benchmark/types.py`
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Write failing test for config/schema import**

```python
# backend/tests/test_benchmark_generator.py
from benchmark.config import BENCHMARK_SEEDS
from benchmark.types import BenchmarkInstance

def test_benchmark_config_and_types_importable():
    assert len(BENCHMARK_SEEDS) >= 10
    assert BenchmarkInstance is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_benchmark_generator.py::test_benchmark_config_and_types_importable -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement minimal scaffold**

- Add benchmark package and basic config constants:
  - seeds: `202601..202620`
  - scales: `small(50,5)`, `medium(100,10)`, `large(200,20)`
  - time limits: 30/60/120 sec
- Add minimal typed structures:
  - `Node`, `Vehicle`, `BenchmarkInstance`, `RunResult`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_benchmark_generator.py::test_benchmark_config_and_types_importable -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/benchmark backend/tests/test_benchmark_generator.py backend/pyproject.toml
git commit -m "chore(benchmark): scaffold benchmark module and config"
```

---

### Task 2: Deterministic instance generator

**Files:**
- Create: `backend/benchmark/generate_instances.py`
- Modify: `backend/benchmark/types.py`
- Test: `backend/tests/test_benchmark_generator.py`

- [ ] **Step 1: Write failing reproducibility tests**

```python
from benchmark.generate_instances import generate_instance

def test_same_seed_same_instance():
    a = generate_instance(scale="small", seed=202601)
    b = generate_instance(scale="small", seed=202601)
    assert a.model_dump() == b.model_dump()


def test_different_seed_different_instance():
    a = generate_instance(scale="small", seed=202601)
    b = generate_instance(scale="small", seed=202602)
    assert a.model_dump() != b.model_dump()
```

- [ ] **Step 2: Run tests to verify fail**

Run: `cd backend && uv run pytest tests/test_benchmark_generator.py -v`
Expected: FAIL (function missing).

- [ ] **Step 3: Implement generator**

- Use `random.Random(seed)` only (no global RNG).
- Output includes depot, customers, order demands, vehicles.
- Enforce feasible total capacity ratio (e.g., total capacity >= 1.15 * total demand).
- Save JSON instances under `benchmark/datasets/instances/<scale>/seed_<seed>.json`.

- [ ] **Step 4: Run tests to pass**

Run: `cd backend && uv run pytest tests/test_benchmark_generator.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/benchmark/generate_instances.py backend/tests/test_benchmark_generator.py backend/benchmark/types.py
git commit -m "feat(benchmark): add deterministic multi-scale instance generator"
```

---

### Task 3: Distance layer abstraction (Haversine + ORS)

**Files:**
- Create: `backend/benchmark/distance.py`
- Modify: `backend/benchmark/config.py`
- Test: `backend/tests/test_benchmark_feasibility.py`

- [ ] **Step 1: Write failing tests**

```python
from benchmark.distance import build_haversine_matrix

def test_distance_matrix_square_and_zero_diag(sample_instance):
    m = build_haversine_matrix(sample_instance.nodes)
    n = len(sample_instance.nodes)
    assert len(m) == n
    assert all(len(r) == n for r in m)
    assert all(m[i][i] == 0 for i in range(n))
```

- [ ] **Step 2: Run test and fail**

Run: `cd backend && uv run pytest tests/test_benchmark_feasibility.py::test_distance_matrix_square_and_zero_diag -v`
Expected: FAIL.

- [ ] **Step 3: Implement distance module**

- `build_haversine_matrix(nodes)` for Layer A.
- `build_ors_matrix(nodes)` with cache + retry for Layer B.
- `get_distance_matrix(mode="haversine"|"ors")` abstraction.

- [ ] **Step 4: Run test and pass**

Run: `cd backend && uv run pytest tests/test_benchmark_feasibility.py::test_distance_matrix_square_and_zero_diag -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/benchmark/distance.py backend/benchmark/config.py backend/tests/test_benchmark_feasibility.py
git commit -m "feat(benchmark): add dual-layer distance matrix abstraction"
```

---

### Task 4: Baseline A1 Random/Nearest

**Files:**
- Create: `backend/benchmark/algorithms/random_nearest.py`
- Modify: `backend/benchmark/types.py`
- Test: `backend/tests/test_benchmark_feasibility.py`

- [ ] **Step 1: Write failing feasibility test**

```python
from benchmark.algorithms.random_nearest import solve_random_nearest

def test_random_nearest_returns_feasible_solution(sample_instance, sample_matrix):
    out = solve_random_nearest(sample_instance, sample_matrix, seed=1)
    assert out.feasible is True
    assert out.total_distance > 0
```

- [ ] **Step 2: Run test and fail**

Run: `cd backend && uv run pytest tests/test_benchmark_feasibility.py::test_random_nearest_returns_feasible_solution -v`
Expected: FAIL.

- [ ] **Step 3: Implement solver**

- Deterministic random customer order with seed.
- Greedy nearest insertion per vehicle under capacity hard constraints.
- If infeasible, return explicit `feasible=False` and reason.

- [ ] **Step 4: Run test and pass**

Run: `cd backend && uv run pytest tests/test_benchmark_feasibility.py::test_random_nearest_returns_feasible_solution -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/benchmark/algorithms/random_nearest.py backend/tests/test_benchmark_feasibility.py backend/benchmark/types.py
git commit -m "feat(benchmark): implement random-nearest baseline"
```

---

### Task 5: Baseline A2 GA-only

**Files:**
- Create: `backend/benchmark/algorithms/ga_only.py`
- Modify: `backend/benchmark/config.py`
- Test: `backend/tests/test_benchmark_feasibility.py`

- [ ] **Step 1: Write failing test for GA-only output**

```python
from benchmark.algorithms.ga_only import solve_ga_only

def test_ga_only_returns_metrics(sample_instance, sample_matrix):
    out = solve_ga_only(sample_instance, sample_matrix, seed=7)
    assert out.total_distance > 0
    assert out.solve_time_sec >= 0
```

- [ ] **Step 2: Run test and fail**

Run: `cd backend && uv run pytest tests/test_benchmark_feasibility.py::test_ga_only_returns_metrics -v`
Expected: FAIL.

- [ ] **Step 3: Implement GA-only**

- Global chromosome over all customers.
- Decode to multi-vehicle routes using capacity-aware split.
- Operators: tournament, OX crossover, swap mutation, elitism.
- Stop by shared compute budget (`time_limit` or `max_evals`).

- [ ] **Step 4: Run test and pass**

Run: `cd backend && uv run pytest tests/test_benchmark_feasibility.py::test_ga_only_returns_metrics -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/benchmark/algorithms/ga_only.py backend/benchmark/config.py backend/tests/test_benchmark_feasibility.py
git commit -m "feat(benchmark): implement GA-only baseline"
```

---

### Task 6: Baseline A3 OR-Tools wrapper

**Files:**
- Create: `backend/benchmark/algorithms/ortools_cvrp.py`
- Test: `backend/tests/test_benchmark_feasibility.py`

- [ ] **Step 1: Write failing test for OR-Tools baseline**

```python
from benchmark.algorithms.ortools_cvrp import solve_ortools_cvrp

def test_ortools_baseline_runs(sample_instance, sample_matrix):
    out = solve_ortools_cvrp(sample_instance, sample_matrix, time_limit_sec=10)
    assert out.feasible in [True, False]
    assert out.solve_time_sec >= 0
```

- [ ] **Step 2: Run test and fail**

Run: `cd backend && uv run pytest tests/test_benchmark_feasibility.py::test_ortools_baseline_runs -v`
Expected: FAIL.

- [ ] **Step 3: Implement wrapper**

- Reuse existing project OR-Tools modeling style.
- Keep strict same constraints as other methods.
- Expose objective, runtime, feasibility, route count.

- [ ] **Step 4: Run test and pass**

Run: `cd backend && uv run pytest tests/test_benchmark_feasibility.py::test_ortools_baseline_runs -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/benchmark/algorithms/ortools_cvrp.py backend/tests/test_benchmark_feasibility.py
git commit -m "feat(benchmark): add OR-Tools CVRP strong baseline"
```

---

### Task 7: Main method A4 KMeans+GA

**Files:**
- Create: `backend/benchmark/algorithms/kmeans_ga.py`
- Modify: `backend/benchmark/config.py`
- Test: `backend/tests/test_benchmark_feasibility.py`

- [ ] **Step 1: Write failing tests for method output and constraints**

```python
from benchmark.algorithms.kmeans_ga import solve_kmeans_ga

def test_kmeans_ga_runs_and_respects_capacity(sample_instance, sample_matrix):
    out = solve_kmeans_ga(sample_instance, sample_matrix, seed=11)
    assert out.solve_time_sec >= 0
    assert out.capacity_violations == 0
```

- [ ] **Step 2: Run test and fail**

Run: `cd backend && uv run pytest tests/test_benchmark_feasibility.py::test_kmeans_ga_runs_and_respects_capacity -v`
Expected: FAIL.

- [ ] **Step 3: Implement method**

- KMeans clustering with fixed `n_init=20`.
- Capacity-aware cluster repair.
- Vehicle assignment by capacity-demand matching.
- Per-cluster GA optimization with shared parameter template.
- Aggregate route metrics and feasibility diagnostics.

- [ ] **Step 4: Run test and pass**

Run: `cd backend && uv run pytest tests/test_benchmark_feasibility.py::test_kmeans_ga_runs_and_respects_capacity -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/benchmark/algorithms/kmeans_ga.py backend/benchmark/config.py backend/tests/test_benchmark_feasibility.py
git commit -m "feat(benchmark): implement two-stage KMeans+GA algorithm"
```

---

### Task 8: Unified runner and raw logging

**Files:**
- Create: `backend/benchmark/runner.py`
- Create: `backend/benchmark/run_suite.py`
- Test: `backend/tests/test_benchmark_runner.py`

- [ ] **Step 1: Write failing E2E smoke test**

```python
from benchmark.run_suite import run_small_smoke_suite

def test_smoke_suite_outputs_raw_csv(tmp_path):
    output = run_small_smoke_suite(output_dir=tmp_path)
    assert output.raw_csv_path.exists()
```

- [ ] **Step 2: Run test and fail**

Run: `cd backend && uv run pytest tests/test_benchmark_runner.py::test_smoke_suite_outputs_raw_csv -v`
Expected: FAIL.

- [ ] **Step 3: Implement runners**

- `runner.py`: run one `(instance, algorithm, seed)` and return `RunResult`.
- `run_suite.py`: loops over scales/seeds/algorithms, writes `results/raw/*.csv`.
- Include environment fingerprint: CPU model, Python version, commit hash.

- [ ] **Step 4: Run test and pass**

Run: `cd backend && uv run pytest tests/test_benchmark_runner.py::test_smoke_suite_outputs_raw_csv -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/benchmark/runner.py backend/benchmark/run_suite.py backend/tests/test_benchmark_runner.py
git commit -m "feat(benchmark): add unified benchmark runner and raw logging"
```

---

### Task 9: Statistics, significance tests, and plots

**Files:**
- Create: `backend/benchmark/analyze.py`
- Create: `backend/benchmark/plot.py`
- Create: `docs/benchmark-methodology.md`

- [ ] **Step 1: Write failing test for summary schema**

```python
from benchmark.analyze import summarize_results

def test_summary_contains_core_metrics(sample_raw_results_csv):
    df = summarize_results(sample_raw_results_csv)
    required = {"algorithm", "scale", "mean_distance", "mean_time", "feasible_rate", "ci95_distance"}
    assert required.issubset(df.columns)
```

- [ ] **Step 2: Run test and fail**

Run: `cd backend && uv run pytest tests/test_benchmark_runner.py::test_summary_contains_core_metrics -v`
Expected: FAIL.

- [ ] **Step 3: Implement analyze + plot**

- Compute: mean/std/95%CI, distance gap %, time ratio, feasibility rate.
- Significance: paired Wilcoxon or t-test (check normality first).
- Effect size: Cliff’s delta or Cohen’s d.
- Plot outputs:
  - Quality-time Pareto scatter
  - Distance boxplot by algorithm
  - Runtime scaling curve by N

- [ ] **Step 4: Run test and pass**

Run: `cd backend && uv run pytest tests/test_benchmark_runner.py::test_summary_contains_core_metrics -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/benchmark/analyze.py backend/benchmark/plot.py docs/benchmark-methodology.md backend/tests/test_benchmark_runner.py
git commit -m "feat(benchmark): add statistical analysis and paper-ready plots"
```

---

### Task 10: Layer B ORS validation and final reproduction docs

**Files:**
- Modify: `backend/benchmark/run_suite.py`
- Modify: `backend/benchmark/README.md`
- Modify: `README.md`

- [ ] **Step 1: Write failing test for ORS validation mode contract**

```python
from benchmark.run_suite import run_ors_validation_subset

def test_ors_validation_returns_subset_metrics(tmp_path):
    out = run_ors_validation_subset(output_dir=tmp_path, per_scale_samples=2)
    assert out.summary_csv_path.exists()
```

- [ ] **Step 2: Run test and fail**

Run: `cd backend && uv run pytest tests/test_benchmark_runner.py::test_ors_validation_returns_subset_metrics -v`
Expected: FAIL.

- [ ] **Step 3: Implement ORS subset mode + docs**

- Add sampled subset runner for each scale.
- Add caching and retry policies for ORS requests.
- Document exact commands:
  - generate instances
  - run Layer A full suite
  - run Layer B subset
  - build stats and figures

- [ ] **Step 4: Run tests and smoke benchmark**

Run:
- `cd backend && uv run pytest tests -v`
- `cd backend && uv run python -m benchmark.run_suite --mode smoke`
- `cd backend && uv run python -m benchmark.analyze --input benchmark/results/raw/smoke.csv`

Expected:
- test suite PASS
- raw/summary CSV and plots generated.

- [ ] **Step 5: Commit**

```bash
git add backend/benchmark backend/tests README.md
git commit -m "docs(benchmark): finalize dual-layer protocol and reproduction guide"
```

---

## 2. Benchmark Protocol (Execution Order)

- [ ] Generate deterministic instances for all scales and seeds.
- [ ] Run Layer A full experiments (`haversine`).
- [ ] Run Layer B sampled experiments (`ors`).
- [ ] Aggregate and run significance tests.
- [ ] Export paper tables and figures.
- [ ] Draft conclusion statements with effect sizes and p-values.

---

## 3. Acceptance Criteria

- [ ] Re-running with same seeds yields identical Layer A raw results (within floating tolerance).
- [ ] All four algorithms run on all scales (or explicit timeout/fail records captured).
- [ ] At least one statistically significant win for `KMeans+GA` on quality-time balance metric.
- [ ] Full reproduction possible from command list in `backend/benchmark/README.md`.
- [ ] Paper-ready artifacts generated: summary table, significance table, 3 core figures.

---

## 4. Suggested Commands for Final Reproduction

```bash
cd backend
uv run python -m benchmark.generate_instances
uv run python -m benchmark.run_suite --layer A
uv run python -m benchmark.run_suite --layer B --per-scale-samples 5
uv run python -m benchmark.analyze --input benchmark/results/raw --output benchmark/results/summary
uv run python -m benchmark.plot --input benchmark/results/summary --output benchmark/plots
```

---

## 5. Risks and Controls

- ORS quota/network instability: keep Layer B sampled + cache matrix files.
- Non-determinism from hidden RNG: enforce seeded local RNG in all stochastic modules.
- Unfair tuning accusations: use shared compute budget and document all parameters.
- Infeasible instances: enforce generator feasibility checks and log skipped instances with reasons.

---

## 6. Handoff Notes for Execution Agent

- Use `superpowers:subagent-driven-development` to execute one task at a time.
- Do not mix major tasks in one commit.
- Run verification commands before claiming completion.
- Keep docs aligned with actual implementation (remove stale GA/KMeans claims if code differs).
