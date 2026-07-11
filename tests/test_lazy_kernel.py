from __future__ import annotations

import pytest

from openai4s.kernel.lazy import LazyKernel


class _Kernel:
    def __init__(self) -> None:
        self.cells: list[tuple[str, str]] = []
        self.closed = False
        self.generation = 7

    def execute(self, code: str, *, origin: str) -> dict:
        self.cells.append((origin, code))
        return {"stdout": code, "error": None}

    def is_alive(self) -> bool:
        return not self.closed

    def interrupt(self) -> None:
        self.cells.append(("system", "interrupt"))

    def shutdown(self) -> None:
        self.closed = True


def test_context_without_code_never_creates_a_worker():
    created: list[_Kernel] = []

    with LazyKernel(lambda: created.append(_Kernel()) or created[-1]) as lazy:
        assert lazy.spawned is False
        assert lazy.generation is None
        assert lazy.is_alive() is False

    assert created == []


def test_first_cell_bootstraps_once_reuses_and_detaches_worker():
    created: list[_Kernel] = []
    published: list[_Kernel | None] = []

    def factory() -> _Kernel:
        kernel = _Kernel()
        created.append(kernel)
        return kernel

    lazy = LazyKernel(
        factory,
        bootstrap=lambda kernel: kernel.execute("bootstrap", origin="system"),
        publish=published.append,
    )

    first = lazy.execute("one", origin="agent")
    second = lazy.execute("two", origin="agent")

    assert first["stdout"] == "one" and second["stdout"] == "two"
    assert len(created) == 1
    assert created[0].cells == [
        ("system", "bootstrap"),
        ("agent", "one"),
        ("agent", "two"),
    ]
    assert lazy.generation == 7
    lazy.shutdown()
    assert created[0].closed is True
    assert published == [created[0], None]


def test_bootstrap_failure_does_not_publish_a_broken_worker():
    kernel = _Kernel()
    published: list[_Kernel | None] = []

    def fail(_kernel: _Kernel) -> None:
        raise RuntimeError("bootstrap failed")

    lazy = LazyKernel(lambda: kernel, bootstrap=fail, publish=published.append)

    with pytest.raises(RuntimeError, match="bootstrap failed"):
        lazy.execute("never", origin="agent")

    assert lazy.spawned is False
    assert kernel.closed is True
    assert published == [kernel, None]
