"""Name → adapter, so the pipeline asks for a source instead of importing it.

There are no built-in adapters yet: Fesofi arrives in A6 and Colnect in A3, and
each will register itself here. Keeping the registry in its own module is what
stops the pipeline from growing an `if source == ...` chain later.
"""

from __future__ import annotations

from typing import Dict, List, Type

from ai_api.sources.base import SourceAdapter


_ADAPTERS: Dict[str, Type[SourceAdapter]] = {}


def register(adapter: Type[SourceAdapter]) -> Type[SourceAdapter]:
    """Register an adapter class under its `name`, and return it."""
    if not adapter.name:
        raise ValueError("An adapter needs a name to be registered")
    _ADAPTERS[adapter.name] = adapter
    return adapter


def get(name: str) -> Type[SourceAdapter]:
    """Return the adapter registered under `name`."""
    try:
        return _ADAPTERS[name]
    except KeyError as error:
        raise KeyError(
            f"Unknown source: {name}. Registered: {sorted(_ADAPTERS)}"
        ) from error


def available() -> List[str]:
    """Return the registered source names, sorted."""
    return sorted(_ADAPTERS)


def unregister(name: str) -> None:
    """Forget an adapter; used by tests so the registry does not leak."""
    _ADAPTERS.pop(name, None)


def clear() -> None:
    """Forget every adapter; used by tests."""
    _ADAPTERS.clear()
