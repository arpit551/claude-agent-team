"""File system watcher for real-time updates."""

import asyncio
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
from watchdog.observers import Observer


class TaskFileHandler(FileSystemEventHandler):
    """Handles file system events for task files."""

    def __init__(self, callback: Callable[[], None], debounce_ms: int = 100):
        self.callback = callback
        self.debounce_ms = debounce_ms
        self._debounce_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the event loop for async callbacks."""
        self._loop = loop

    def on_modified(self, event):
        """Called when a file is modified."""
        if event.is_directory:
            return
        if event.src_path.endswith(".json"):
            self._schedule_callback()

    def on_created(self, event):
        """Called when a file is created."""
        if event.is_directory:
            return
        if event.src_path.endswith(".json"):
            self._schedule_callback()

    def _schedule_callback(self):
        """Schedule callback with debouncing."""
        if self._loop is None:
            # Fallback to sync callback
            self.callback()
            return

        # Cancel previous debounce task if exists
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()

        # Schedule new debounced callback
        async def debounced():
            await asyncio.sleep(self.debounce_ms / 1000)
            self.callback()

        self._debounce_task = self._loop.create_task(debounced())


class TaskWatcher:
    """Watches Claude Code's todo directory for changes."""

    def __init__(
        self,
        todos_path: Optional[Path] = None,
        callback: Optional[Callable[[], None]] = None,
    ):
        self.todos_path = todos_path or Path.home() / ".claude" / "todos"
        self.callback = callback or (lambda: None)
        self.handler = TaskFileHandler(self.callback)
        self.observer = Observer()
        self._running = False

    def start(self):
        """Start watching for file changes."""
        if self._running:
            return

        if not self.todos_path.exists():
            self.todos_path.mkdir(parents=True, exist_ok=True)

        self.observer.schedule(self.handler, str(self.todos_path), recursive=False)
        self.observer.start()
        self._running = True

    def stop(self):
        """Stop watching for file changes."""
        if not self._running:
            return

        self.observer.stop()
        self.observer.join(timeout=2)
        self._running = False

    def set_callback(self, callback: Callable[[], None]):
        """Update the callback function."""
        self.callback = callback
        self.handler.callback = callback

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the event loop for async operations."""
        self.handler.set_loop(loop)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
