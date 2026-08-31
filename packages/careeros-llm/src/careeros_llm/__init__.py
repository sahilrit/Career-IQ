"""careeros_llm: the LLM gateway.

Business logic imports ``LLMGateway`` and ``LLMTask`` and nothing else about
AI. Which vendor answers is a configuration and runtime-health question, not
something any feature knows.
"""

from careeros_llm.bridge import GatewayAIClient, client_for
from careeros_llm.cli_provider import (
    CLI_SPECS,
    CliProvider,
    CliSpec,
    available_cli_providers,
    looks_like_cli_error,
)
from careeros_llm.config import DEFAULT_PRIORITY, LLMConfig
from careeros_llm.exceptions import (
    LLMGatewayError,
    NoProviderAvailableError,
    ProviderCallError,
)
from careeros_llm.gateway import LLMGateway, LLMResponse, build_providers
from careeros_llm.models import LLMRun, LLMTask, ProviderHealth, ProviderStatus
from careeros_llm.provider import ApiKeyProvider, LLMProvider

__all__ = [
    "CLI_SPECS",
    "DEFAULT_PRIORITY",
    "ApiKeyProvider",
    "CliProvider",
    "CliSpec",
    "GatewayAIClient",
    "LLMConfig",
    "LLMGateway",
    "LLMGatewayError",
    "LLMProvider",
    "LLMResponse",
    "LLMRun",
    "LLMTask",
    "NoProviderAvailableError",
    "ProviderCallError",
    "ProviderHealth",
    "ProviderStatus",
    "available_cli_providers",
    "build_providers",
    "client_for",
    "looks_like_cli_error",
]
