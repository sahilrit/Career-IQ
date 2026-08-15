"""Tests for build_context."""

from __future__ import annotations

from careeros_career_brain import CareerBrain, Identity
from careeros_cli.context import build_context


def test_build_context_persists_across_separate_calls(tmp_path, fake_registry):
    first = build_context(tmp_path, provider_registry=fake_registry)
    brain = CareerBrain(identity=Identity(full_name="Ada", email="ada@example.com"))
    first.repository.save(brain)

    second = build_context(tmp_path, provider_registry=fake_registry)
    reloaded = second.repository.load(brain.identity.id)

    assert reloaded.identity.full_name == "Ada"


def test_build_context_defaults_to_a_real_registry_without_network_calls(tmp_path):
    # Constructing the context (and the RemoteOKProvider inside it) must
    # never touch the network — only calling .search()/.health_check() does.
    context = build_context(tmp_path)
    assert context.provider_registry.get("remoteok") is not None
