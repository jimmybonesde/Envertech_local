"""Unit tests for the poll-interval option handling.

Home Assistant is stubbed so the coordinator can run standalone.
"""

from __future__ import annotations

from tests.test_coordinator import _make_coordinator


def _fake_entry(options: dict):
    class _Entry:
        def __init__(self) -> None:
            self.options = options
            self.created_tasks: list = []

        def async_create_background_task(self, hass, coro, name):
            # Simulate a running task.
            task = _FakeTask()
            self.created_tasks.append(task)
            return task

    return _Entry()


class _FakeTask:
    def __init__(self) -> None:
        self.cancelled = False
        self._done = False

    def done(self) -> bool:
        return self._done

    def cancel(self) -> None:
        self.cancelled = True
        self._done = True


def test_async_start_reads_poll_interval_from_options() -> None:
    coord = _make_coordinator()
    entry = _fake_entry({"poll_interval": 30})
    coord.async_start(entry)
    assert coord.poll_interval == 30
    assert entry.created_tasks


def test_async_start_uses_default_when_option_missing() -> None:
    coord = _make_coordinator()
    entry = _fake_entry({})
    coord.async_start(entry)
    assert coord.poll_interval == 5


def test_set_poll_interval_restarts_stream() -> None:
    coord = _make_coordinator()
    entry = _fake_entry({"poll_interval": 5})
    coord.async_start(entry)
    first_task = entry.created_tasks[-1]
    assert first_task.done() is False

    coord.async_set_poll_interval(10)
    assert coord.poll_interval == 10
    assert first_task.cancelled
    # A new stream task must have been created.
    assert len(entry.created_tasks) == 2
    assert entry.created_tasks[-1] is not first_task
    assert entry.created_tasks[-1].done() is False
