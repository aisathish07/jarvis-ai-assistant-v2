import logging
import pathlib

from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

log = logging.getLogger("AI_Assistant.PluginWatcher")


class _ReloadHandler(FileSystemEventHandler):
    def __init__(self, manager):
        self.mgr = manager

    def on_modified(self, evt: FileModifiedEvent):
        if evt.is_directory:
            return
        if pathlib.Path(evt.src_path).suffix == ".py":
            log.info("♻️  %s changed – reloading skills", evt.src_path)
            self.mgr.plugins.clear()
            self.mgr.discover_and_load(self.mgr.assistant_api)


def start_watching(manager, skills_dir: str):
    handler = _ReloadHandler(manager)
    observer = Observer()
    observer.schedule(handler, skills_dir, recursive=False)
    observer.start()
    log.info("👀 Watching %s for changes", skills_dir)
