"""Kernel tests: persistent namespace, print capture, error attribution,
usage accounting, and host_call RPC round-trip (dispatcher stubbed)."""
import pytest

from openai4s.kernel import Kernel


def _echo_dispatcher(method, args):
    if method == "ping":
        return "pong"
    if method == "add":
        return sum(args[0]["nums"])
    raise ValueError(f"unknown method {method}")


def test_print_capture():
    with Kernel(dispatcher=_echo_dispatcher) as k:
        r = k.execute("print('hello')")
        assert r["stdout"] == "hello\n"
        assert r["error"] is None


def test_persistent_namespace():
    with Kernel(dispatcher=_echo_dispatcher) as k:
        k.execute("x = 41")
        r = k.execute("print(x + 1)")
        assert r["stdout"].strip() == "42"


def test_expr_echo():
    with Kernel(dispatcher=_echo_dispatcher) as k:
        r = k.execute("21 * 2")
        assert r["stdout"].strip() == "42"


def test_error_lineno():
    with Kernel(dispatcher=_echo_dispatcher) as k:
        r = k.execute("a = 1\nb = 2\nraise ValueError('boom')")
        assert r["error"] is not None
        assert "ValueError" in r["error"]
        assert r["trace"]["error_lineno"] == 3


def test_usage_accounting():
    with Kernel(dispatcher=_echo_dispatcher) as k:
        r = k.execute("sum(range(1000))")
        u = r["usage"]
        assert set(u) == {"wall_s", "cpu_s", "peak_rss_kb"}
        assert u["wall_s"] >= 0 and u["peak_rss_kb"] > 0


def test_host_call_roundtrip():
    with Kernel(dispatcher=_echo_dispatcher) as k:
        r = k.execute("reply = host._call('ping', [])\n" "print(reply)")
        assert r["stdout"].strip() == "pong"


def test_host_call_with_args():
    with Kernel(dispatcher=_echo_dispatcher) as k:
        r = k.execute("print(host._call('add', [{'nums': [1, 2, 3, 4]}]))")
        assert r["stdout"].strip() == "10"


def test_host_call_error_propagates():
    with Kernel(dispatcher=_echo_dispatcher) as k:
        r = k.execute(
            "try:\n"
            "    host._call('nope', [])\n"
            "except RuntimeError as e:\n"
            "    print('caught:', 'unknown method' in str(e))"
        )
        assert r["stdout"].strip() == "caught: True"


# --- frame-protocol contract tests (PR 10) ---------------------------------
# These lock the CURRENT worker/manager wire contract before any extraction
# of kernel/manager internals. They follow the existing Kernel(...) patterns
# exactly — do not add new frame types or reader loops here.


def _contract_dispatcher(method, args):
    if method == "soft":
        # single-key {"error": ...} is the soft-fail shape: the manager must
        # route it onto the error channel, NOT hand it back as data.
        return {"error": "soft failure from host"}
    if method == "error_plus_data":
        # an error key WITH siblings is ordinary data, not a soft-fail.
        return {"error": "x", "detail": "still data"}
    if method == "none":
        return None
    raise ValueError(f"unknown method {method}")


def test_response_frame_shape():
    """The final response frame carries exactly the documented key set."""
    with Kernel(dispatcher=_echo_dispatcher) as k:
        r = k.execute("print('shape')")
        assert set(r) == {
            "type",
            "id",
            "stdout",
            "stderr",
            "error",
            "interrupted",
            "trace",
            "guards",
            "usage",
        }
        assert r["type"] == "response"
        assert r["interrupted"] is False
        assert set(r["trace"]) == {"error_lineno", "error_call"}
        assert isinstance(r["guards"], dict)


def test_stderr_captured_separately():
    with Kernel(dispatcher=_echo_dispatcher) as k:
        r = k.execute("import sys\nsys.stderr.write('warn!\\n')\nprint('out')")
        assert r["stdout"].strip() == "out"
        assert "warn!" in r["stderr"]
        assert r["error"] is None


def test_stdout_chunks_stream_via_on_chunk():
    """stdout_chunk frames stream live; on_chunk sees the same text the final
    response frame reports."""
    chunks = []
    with Kernel(dispatcher=_echo_dispatcher) as k:
        r = k.execute("print('live')", on_chunk=chunks.append)
        assert "live" in "".join(chunks)
        assert r["stdout"] == "live\n"


def test_host_call_soft_fail_single_key_error_dict():
    """Dispatcher returning {'error': msg} (and nothing else) surfaces in the
    kernel as a RuntimeError('host.<method> error: <msg>') — the soft-fail
    contract every host handler relies on."""
    with Kernel(dispatcher=_contract_dispatcher) as k:
        r = k.execute(
            "try:\n"
            "    host._call('soft', [])\n"
            "except RuntimeError as e:\n"
            "    print('caught:', e)"
        )
        assert r["error"] is None
        assert "caught: host.soft error: soft failure from host" in r["stdout"]


def test_host_call_error_key_with_siblings_is_plain_data():
    with Kernel(dispatcher=_contract_dispatcher) as k:
        r = k.execute(
            "d = host._call('error_plus_data', [])\n"
            "print(sorted(d), d['error'], d['detail'])"
        )
        assert r["error"] is None
        assert r["stdout"].strip() == "['detail', 'error'] x still data"


def test_host_call_none_data_roundtrips():
    with Kernel(dispatcher=_contract_dispatcher) as k:
        r = k.execute("print(host._call('none', []) is None)")
        assert r["stdout"].strip() == "True"


def test_host_call_without_dispatcher_errors():
    with Kernel(dispatcher=None) as k:
        r = k.execute(
            "try:\n"
            "    host._call('ping', [])\n"
            "except RuntimeError as e:\n"
            "    print('caught:', e)"
        )
        assert "no host dispatcher configured" in r["stdout"]


def test_system_exit_is_trapped_and_worker_survives():
    """exit()/SystemExit must not kill the worker: it is reported as an error
    and the SAME kernel (same namespace) keeps serving cells."""
    with Kernel(dispatcher=_echo_dispatcher) as k:
        k.execute("x = 7")
        r = k.execute("raise SystemExit(3)")
        assert r["error"] is not None
        assert "SystemExit trapped" in r["error"]
        assert k.is_alive()
        r2 = k.execute("print(x)")  # namespace survived the trapped exit
        assert r2["stdout"].strip() == "7"


def test_restart_bumps_generation_and_resets_namespace():
    with Kernel(dispatcher=_echo_dispatcher) as k:
        assert k.generation == 0
        k.execute("x = 1")
        k.restart()
        assert k.generation == 1
        assert k.is_alive()
        r = k.execute("print('x' in globals())")
        assert r["stdout"].strip() == "False"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
