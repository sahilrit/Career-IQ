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
    MalformedResponseError,
    NoProviderAvailableError,
    ProviderCallError,
)
from careeros_llm.gateway import (
    LLMGateway,
    LLMResponse,
    StructuredResponse,
    build_providers,
)
from careeros_llm.models import (
    FailureKind,
    LLMRun,
    LLMTask,
    ProviderHealth,
    ProviderStatus,
    classify_failure,
)
from careeros_llm.provider import ApiKeyProvider, LLMProvider
from careeros_llm.structured import extract_json, parse_structured, schema_instruction

__all__ = [
    "CLI_SPECS",
    "DEFAULT_PRIORITY",
    "ApiKeyProvider",
    "CliProvider",
    "CliSpec",
    "FailureKind",
    "GatewayAIClient",
    "LLMConfig",
    "LLMGateway",
    "LLMGatewayError",
    "LLMProvider",
    "LLMResponse",
    "LLMRun",
    "LLMTask",
    "MalformedResponseError",
    "NoProviderAvailableError",
    "ProviderCallError",
    "ProviderHealth",
    "ProviderStatus",
    "StructuredResponse",
    "available_cli_providers",
    "build_providers",
    "classify_failure",
    "client_for",
    "extract_json",
    "looks_like_cli_error",
    "parse_structured",
    "schema_instruction",
]
