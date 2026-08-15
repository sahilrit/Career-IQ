"""careeros_skill_marketplace: the AI Skill Marketplace.

The second marketplace section alongside Phase 48's Integrations —
intelligence CareerOS's own packages already provide, and can now be
browsed and searched as a distinct category from external-service
plugins.
"""

from careeros_skill_marketplace.exceptions import SkillMarketplaceError, SkillNotFoundError
from careeros_skill_marketplace.seed_skills import SEED_SKILLS
from careeros_skill_marketplace.skill_listing import AISkillCategory, AISkillListing
from careeros_skill_marketplace.skill_marketplace import AISkillMarketplace
from careeros_skill_marketplace.unified_marketplace import UnifiedMarketplace

__all__ = [
    "SEED_SKILLS",
    "AISkillCategory",
    "AISkillListing",
    "AISkillMarketplace",
    "SkillMarketplaceError",
    "SkillNotFoundError",
    "UnifiedMarketplace",
]
