"""careeros_capability_marketplace: ranking, fallback, parallel
execution, aggregation, and versioning for capability providers —
"which capability do I need?" instead of "which plugin should I call?".
"""

from careeros_capability_marketplace.aggregation import flatten, flatten_and_dedupe
from careeros_capability_marketplace.exceptions import MarketplaceError, NoProviderAvailableError
from careeros_capability_marketplace.marketplace import CapabilityMarketplace, ProviderRecord

__all__ = [
    "CapabilityMarketplace",
    "MarketplaceError",
    "NoProviderAvailableError",
    "ProviderRecord",
    "flatten",
    "flatten_and_dedupe",
]
