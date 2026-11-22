"""Cache deterministica con invalidazione automatica ai cambi dei parametri rilevanti."""

from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from typing import Any, Callable, TypeVar

from kaleido_factory.core.validation import require_int

T = TypeVar("T")


def build_cache_key(namespace: str, params: dict[str, Any]) -> str:
    """Genera una chiave deterministica SHA-256 da namespace e parametri rilevanti."""
    if not isinstance(namespace, str) or not namespace.strip():
        raise ValueError("namespace deve essere una stringa non vuota.")
    if not isinstance(params, dict):
        raise TypeError("params deve essere un dizionario.")
    canonical = json.dumps(params, sort_keys=True, default=str, separators=(",", ":"))
    payload = f"{namespace.strip()}:{canonical}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class ParameterCache:
    """Cache LRU limitata in memoria con invalidazione esplicita per namespace o chiave."""

    def __init__(self, max_entries: int = 128) -> None:
        limit = require_int(max_entries, "max_entries", min_value=1)
        self._max_entries: int = limit
        self._store: OrderedDict[str, tuple[str, Any]] = OrderedDict()

    @property
    def size(self) -> int:
        return len(self._store)

    def get_or_compute(self, namespace: str, params: dict[str, Any], compute_fn: Callable[[], T]) -> tuple[T, bool]:
        """Restituisce (valore, cache_hit) ricalcolando solo se la chiave non e presente."""
        if not callable(compute_fn):
            raise TypeError("compute_fn deve essere richiamabile.")
        ns = namespace.strip() if isinstance(namespace, str) else ""
        key = build_cache_key(ns, params)
        if key in self._store:
            self._store.move_to_end(key)
            return self._store[key][1], True

        value = compute_fn()
        self._store[key] = (ns, value)
        self._store.move_to_end(key)
        while len(self._store) > self._max_entries:
            self._store.popitem(last=False)
        return value, False

    def invalidate_namespace(self, namespace: str) -> int:
        """Rimuove tutte le voci appartenenti a un namespace e ritorna il numero rimosso."""
        ns = namespace.strip() if isinstance(namespace, str) else ""
        keys_to_drop = [k for k, (entry_ns, _) in self._store.items() if entry_ns == ns]
        for k in keys_to_drop:
            del self._store[k]
        return len(keys_to_drop)

    def clear(self) -> None:
        """Svuota completamente la cache."""
        self._store.clear()