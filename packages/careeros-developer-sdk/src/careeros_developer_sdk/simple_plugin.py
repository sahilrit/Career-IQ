"""SimplePlugin: the concrete Plugin implementation PluginBuilder
produces. A developer never subclasses Plugin directly — they get one
of these back from ``.build()``, with their action handlers callable
by name.
"""

from __future__ import annotations

from collections.abc import Callable

from careeros_developer_sdk.exceptions import UnknownActionError
from careeros_plugin_sdk import Plugin, PluginManifest


class SimplePlugin(Plugin):
    def __init__(
        self,
        manifest: PluginManifest,
        action_handlers: dict[str, Callable[..., object]],
        *,
        on_enable: Callable[[], None] | None = None,
        on_disable: Callable[[], None] | None = None,
    ) -> None:
        self._manifest = manifest
        self._action_handlers = dict(action_handlers)
        self._on_enable = on_enable
        self._on_disable = on_disable

    @property
    def manifest(self) -> PluginManifest:
        return self._manifest

    def on_enable(self) -> None:
        if self._on_enable is not None:
            self._on_enable()

    def on_disable(self) -> None:
        if self._on_disable is not None:
            self._on_disable()

    def call_action(self, action_name: str, *args: object, **kwargs: object) -> object:
        if action_name not in self._action_handlers:
            raise UnknownActionError(
                f"Plugin {self._manifest.id!r} has no handler for action {action_name!r}"
            )
        return self._action_handlers[action_name](*args, **kwargs)
