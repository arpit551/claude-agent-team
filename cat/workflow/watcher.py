"""Real-time file watching for agent outputs."""

import logging
from pathlib import Path
from typing import Callable, Optional, Set
from threading import Thread, Event
import time

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None
    FileModifiedEvent = None

from cat.agent.models import AgentRole

logger = logging.getLogger(__name__)


class OutputFileHandler:
    """Base handler for output file changes (fallback without watchdog)."""

    def __init__(self, callback: Callable[[AgentRole, Path], None]):
        self.callback = callback
        self.watched_files: dict[Path, AgentRole] = {}

    def watch(self, file_path: Path, role: AgentRole) -> None:
        """Start watching a file.

        Args:
            file_path: Path to file to watch
            role: Agent role associated with this file
        """
        self.watched_files[file_path] = role
        logger.debug(f"Watching {file_path} for {role.display_name}")

    def unwatch(self, file_path: Path) -> None:
        """Stop watching a file.

        Args:
            file_path: Path to file to stop watching
        """
        if file_path in self.watched_files:
            del self.watched_files[file_path]
            logger.debug(f"Stopped watching {file_path}")

    def trigger(self, file_path: Path) -> None:
        """Manually trigger callback for a file.

        Args:
            file_path: Path that changed
        """
        if file_path in self.watched_files:
            role = self.watched_files[file_path]
            self.callback(role, file_path)


if WATCHDOG_AVAILABLE:
    class WatchdogOutputHandler(FileSystemEventHandler):
        """Handler using watchdog for efficient file watching."""

        def __init__(self, callback: Callable[[AgentRole, Path], None]):
            super().__init__()
            self.callback = callback
            self.watched_files: dict[Path, AgentRole] = {}

        def watch(self, file_path: Path, role: AgentRole) -> None:
            """Start watching a file.

            Args:
                file_path: Path to file to watch
                role: Agent role associated with this file
            """
            self.watched_files[file_path] = role
            logger.debug(f"Watching {file_path} for {role.display_name}")

        def unwatch(self, file_path: Path) -> None:
            """Stop watching a file.

            Args:
                file_path: Path to file to stop watching
            """
            if file_path in self.watched_files:
                del self.watched_files[file_path]
                logger.debug(f"Stopped watching {file_path}")

        def on_modified(self, event):
            """Handle file modification event.

            Args:
                event: File system event
            """
            if event.is_directory:
                return

            file_path = Path(event.src_path)
            if file_path in self.watched_files:
                role = self.watched_files[file_path]
                logger.debug(f"File modified: {file_path} ({role.display_name})")
                self.callback(role, file_path)
else:
    WatchdogOutputHandler = OutputFileHandler  # Fallback to polling


class OutputWatcher:
    """Watch agent output files for changes in real-time."""

    def __init__(
        self,
        output_dir: Path,
        callback: Callable[[AgentRole, Path], None],
        use_watchdog: bool = True,
    ):
        """Initialize output watcher.

        Args:
            output_dir: Directory containing output files
            callback: Function called when file changes (role, file_path)
            use_watchdog: Use watchdog if available (True) or polling (False)
        """
        self.output_dir = output_dir
        self.callback = callback
        self.use_watchdog = use_watchdog and WATCHDOG_AVAILABLE

        # Setup handler
        if self.use_watchdog:
            logger.info("Using watchdog for file monitoring")
            self.handler = WatchdogOutputHandler(self._on_file_change)
            self.observer = Observer()
            self.observer.schedule(self.handler, str(output_dir), recursive=False)
        else:
            if use_watchdog and not WATCHDOG_AVAILABLE:
                logger.warning("watchdog not available, falling back to polling")
            else:
                logger.info("Using polling for file monitoring")
            self.handler = OutputFileHandler(self._on_file_change)
            self.observer = None

        # Polling support (fallback or when watchdog disabled)
        self._polling = False
        self._poll_thread: Optional[Thread] = None
        self._poll_interval = 2.0
        self._stop_event = Event()
        self._last_mtimes: dict[Path, float] = {}

    def _on_file_change(self, role: AgentRole, file_path: Path) -> None:
        """Internal callback wrapper.

        Args:
            role: Agent role
            file_path: Changed file path
        """
        try:
            self.callback(role, file_path)
        except Exception as e:
            logger.error(f"Error in file change callback: {e}", exc_info=True)

    def watch_agent(self, role: AgentRole, output_file: Path) -> None:
        """Start watching an agent's output file.

        Args:
            role: Agent role
            output_file: Path to output file
        """
        if not output_file.exists():
            logger.warning(f"Output file does not exist: {output_file}")
            return

        self.handler.watch(output_file, role)

        # Track mtime for polling
        if not self.use_watchdog:
            self._last_mtimes[output_file] = output_file.stat().st_mtime

    def unwatch_agent(self, output_file: Path) -> None:
        """Stop watching an agent's output file.

        Args:
            output_file: Path to output file
        """
        self.handler.unwatch(output_file)

        if output_file in self._last_mtimes:
            del self._last_mtimes[output_file]

    def start(self) -> None:
        """Start watching for file changes."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.use_watchdog and self.observer:
            self.observer.start()
            logger.info("Started watchdog file monitoring")
        else:
            # Start polling thread
            self._polling = True
            self._stop_event.clear()
            self._poll_thread = Thread(target=self._poll_files, daemon=True)
            self._poll_thread.start()
            logger.info("Started polling file monitoring")

    def stop(self) -> None:
        """Stop watching for file changes."""
        if self.use_watchdog and self.observer:
            self.observer.stop()
            self.observer.join(timeout=5.0)
            logger.info("Stopped watchdog file monitoring")
        else:
            # Stop polling thread
            self._polling = False
            self._stop_event.set()
            if self._poll_thread:
                self._poll_thread.join(timeout=5.0)
            logger.info("Stopped polling file monitoring")

    def _poll_files(self) -> None:
        """Poll files for changes (fallback when watchdog unavailable)."""
        while self._polling and not self._stop_event.is_set():
            for file_path, role in list(self.handler.watched_files.items()):
                try:
                    if not file_path.exists():
                        continue

                    current_mtime = file_path.stat().st_mtime
                    last_mtime = self._last_mtimes.get(file_path, 0)

                    if current_mtime > last_mtime:
                        logger.debug(f"Detected change in {file_path}")
                        self._last_mtimes[file_path] = current_mtime
                        self._on_file_change(role, file_path)

                except Exception as e:
                    logger.debug(f"Error polling {file_path}: {e}")

            # Wait for next poll
            self._stop_event.wait(self._poll_interval)

    def is_running(self) -> bool:
        """Check if watcher is running.

        Returns:
            True if watching for changes
        """
        if self.use_watchdog and self.observer:
            return self.observer.is_alive()
        else:
            return self._polling

    def watched_files(self) -> Set[Path]:
        """Get set of currently watched files.

        Returns:
            Set of watched file paths
        """
        return set(self.handler.watched_files.keys())


def create_watcher(
    output_dir: Path,
    callback: Callable[[AgentRole, Path], None],
    prefer_watchdog: bool = True,
) -> OutputWatcher:
    """Create an output watcher.

    Args:
        output_dir: Directory containing output files
        callback: Function called when file changes
        prefer_watchdog: Prefer watchdog over polling if available

    Returns:
        OutputWatcher instance
    """
    return OutputWatcher(output_dir, callback, use_watchdog=prefer_watchdog)
