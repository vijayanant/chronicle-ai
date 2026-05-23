import asyncio
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .indexer import LibrarianIndexer
from .guardian import GuardianAgent

from .utils.logging import get_logger

logger = get_logger()

class ChronicleHandler(FileSystemEventHandler):
    """
    Handles file system events for the blog content directory.
    """
    def __init__(self, indexer: LibrarianIndexer, guardian: GuardianAgent, loop: asyncio.AbstractEventLoop):
        self.indexer = indexer
        self.guardian = guardian
        self.loop = loop
        # Simple debounce mechanism to avoid multiple triggers on single save
        self.last_triggered = {} 
        self.debounce_seconds = 2

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return
            
        current_time = time.time()
        last_time = self.last_triggered.get(event.src_path, 0)
        
        if (current_time - last_time) > self.debounce_seconds:
            logger.info(f"[Observer] Change detected in {event.src_path}")
            asyncio.run_coroutine_threadsafe(self.indexer.index_file(event.src_path), self.loop)
            logger.info(f"[Observer] Context update scheduled.")
            self.last_triggered[event.src_path] = current_time

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            logger.info(f"[Observer] New post created: {event.src_path}")
            asyncio.run_coroutine_threadsafe(self.indexer.index_file(event.src_path), self.loop)

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            logger.info(f"[Observer] Post deleted: {event.src_path}")
            asyncio.run_coroutine_threadsafe(self.indexer.delete_file(event.src_path), self.loop)

async def start_watching(path_to_watch: str, indexer: LibrarianIndexer, guardian: GuardianAgent):
    """
    Starts the background observer service.
    """
    loop = asyncio.get_running_loop()
    event_handler = ChronicleHandler(indexer, guardian, loop)
    observer = Observer()
    observer.schedule(event_handler, path_to_watch, recursive=True)
    observer.start()
    
    logger.info(f"--- Chronicle Observer Active ---")
    logger.info(f"Watching: {path_to_watch}")
    logger.info(f"Press Ctrl+C to stop.")
    
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        observer.stop()
        logger.info("Observer stopping...")
    except KeyboardInterrupt:
        observer.stop()
        print("\nObserver stopped.")
    observer.join()
