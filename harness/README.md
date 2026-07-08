# Harness

This directory is the future home for scenario runners, fake providers,
golden traces, offline evals, and smoke scripts. It is a **skeleton**: only
this README and `.gitkeep` placeholders live here for now. No code has been
moved out of `tests/`, and nothing in `harness/` is collected by the default
pytest run (`testpaths = ["tests"]` in `pyproject.toml`).

## Why `harness/` exists separately from `tests/`

`tests/` is the **correctness gate**: the offline pytest suite that must pass
on every PR. It asserts current behavior of the runtime (kernel protocol,
host API, gateway serializers, security gates) with fakes and tmp data dirs.
It never needs network, secrets, GPUs, SSH, lab hardware, or a live LLM.

`harness/` is the **evaluation and scenario layer**: infrastructure for
exercising the agent as a whole — end-to-end scenarios, recorded traces,
quality evals, and fake platform providers that those scenarios plug in.
Harness runs may be slower, may be scored rather than pass/fail, and (only
when explicitly opted in) may talk to live external resources. They are not
part of the default PR gate.

Rule of thumb:

- A regression assertion about a specific contract belongs in `tests/`.
- A reusable fake provider, a replayable scenario, a golden trajectory, or a
  scored eval belongs in `harness/`.

## Layout

| Directory | Intended contents |
| --- | --- |
| `scenarios/` | Declarative end-to-end agent scenarios (task prompt, fixtures, expected outcome shape) runnable against a fake or live backend. |
| `providers/` | Fake/offline platform providers (compute, model endpoints, lab) implementing the same contracts as real ones, for use by scenarios and tests. |
| `golden_traces/` | Captured reference trajectories (turn/frame sequences) used for replay comparison and drift detection. |
| `evals/` | Offline eval definitions and scoring code for agent output quality. |
| `smoke/` | Minimal smoke scripts (e.g. one-shot `openai4s run` drivers) for quick manual or CI-optional verification. |

## Ground rules

- **Offline by default.** Nothing in `harness/` may require live network,
  API keys, GPUs, SSH, Docker, a browser, or lab hardware unless the entry
  point is explicitly opt-in and marked with the corresponding pytest marker
  (`external`, `network`, `live_llm`, `gpu`, `ssh`, `docker`, `browser`,
  `lab`) — the same opt-in markers registered in `pyproject.toml`.
- **No secrets.** Harness content must run without secrets by default, and
  default PR CI never provides any.
- **No production code.** Runtime implementation stays in `openai4s/` (and
  `openai4s_compute_provider/`); harness code only drives or fakes it.
- **Core stays stdlib-only.** Harness helpers must not introduce hard
  third-party imports into the core packages.
- **Don't move tests here.** Existing `tests/` files stay where they are;
  any future relocation needs its own PR with collect-only proof that no
  test was dropped.

See `docs/refactor-plan.md` (PR 05 and section D "Harness") for the full
boundary definition.
