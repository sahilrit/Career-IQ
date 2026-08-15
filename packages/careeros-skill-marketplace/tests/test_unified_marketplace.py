"""Tests for the UnifiedMarketplace facade."""

from __future__ import annotations

from careeros_plugin_marketplace import SEED_CATALOG, PluginMarketplace
from careeros_skill_marketplace import AISkillMarketplace, UnifiedMarketplace


def test_search_all_covers_both_sections(skills):
    unified = UnifiedMarketplace(PluginMarketplace(list(SEED_CATALOG)), AISkillMarketplace(skills))
    results = unified.search_all("remoteok")
    assert len(results["integrations"]) == 1
    assert results["ai_skills"] == []


def test_search_all_finds_ai_skill_matches(skills):
    unified = UnifiedMarketplace(PluginMarketplace(list(SEED_CATALOG)), AISkillMarketplace(skills))
    results = unified.search_all("shopify")
    assert any(skill.skill_id == "shopify-cro-audit" for skill in results["ai_skills"])
