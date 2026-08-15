"""Tests for WorkingMemory, using an injectable fake clock (no real sleeps)."""

from __future__ import annotations

from careeros_memory import WorkingMemory


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_set_then_get_returns_the_value():
    memory = WorkingMemory(clock=_FakeClock())
    memory.set("current_task", "researching Acme")
    assert memory.get("current_task") == "researching Acme"


def test_get_missing_key_returns_default():
    memory = WorkingMemory(clock=_FakeClock())
    assert memory.get("missing", "fallback") == "fallback"


def test_entry_without_ttl_never_expires():
    clock = _FakeClock()
    memory = WorkingMemory(clock=clock)
    memory.set("current_task", "researching Acme")
    clock.advance(10_000)
    assert memory.get("current_task") == "researching Acme"


def test_entry_expires_after_ttl():
    clock = _FakeClock()
    memory = WorkingMemory(clock=clock)
    memory.set("current_task", "researching Acme", ttl_seconds=5)
    clock.advance(6)
    assert memory.get("current_task") is None


def test_entry_survives_before_ttl_elapses():
    clock = _FakeClock()
    memory = WorkingMemory(clock=clock)
    memory.set("current_task", "researching Acme", ttl_seconds=5)
    clock.advance(4)
    assert memory.get("current_task") == "researching Acme"


def test_delete_removes_the_key():
    memory = WorkingMemory(clock=_FakeClock())
    memory.set("current_task", "researching Acme")
    memory.delete("current_task")
    assert memory.get("current_task") is None


def test_clear_removes_everything():
    memory = WorkingMemory(clock=_FakeClock())
    memory.set("a", 1)
    memory.set("b", 2)
    memory.clear()
    assert memory.keys() == []


def test_keys_excludes_expired_entries():
    clock = _FakeClock()
    memory = WorkingMemory(clock=clock)
    memory.set("expires", "soon", ttl_seconds=1)
    memory.set("stays", "forever")
    clock.advance(2)
    assert memory.keys() == ["stays"]
