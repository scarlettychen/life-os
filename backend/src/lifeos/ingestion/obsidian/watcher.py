"""Watch an Obsidian vault and sync on file changes."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class DebouncedVaultHandler(FileSystemEventHandler):
    """Debounce rapid file events into a single sync callback."""

    def __init__(self, callback: Callable[[], None], *, debounce_seconds: float = 1.0) -> None:
        self._callback = callback
        self._debounce_seconds = debounce_seconds
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = str(event.src_path)
        if not path.endswith(".md"):
            return
        self._schedule()

    def _schedule(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce_seconds, self._run)
            self._timer.daemon = True
            self._timer.start()

    def _run(self) -> None:
        try:
            self._callback()
        except Exception:
            logger.exception("Vault sync failed during watch")


def watch_vault(
    vault_path: Path,
    callback: Callable[[], None],
    *,
    debounce_seconds: float = 1.0,
) -> Any:
    """Start watching ``vault_path``. Returns a running observer."""
    handler = DebouncedVaultHandler(callback, debounce_seconds=debounce_seconds)
    observer = Observer()
    observer.schedule(handler, str(vault_path), recursive=True)
    observer.start()
    return observer


def run_watch_loop(observer: Any) -> None:
    """Block until interrupted."""
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
