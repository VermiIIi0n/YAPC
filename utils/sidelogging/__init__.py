# -*- coding: utf-8 -*-
from time import sleep
from threading import Thread, current_thread, Lock
from queue import Queue
from typing import Callable, Protocol, Any
from .MonoLogger import MonoLogger

__all__ = ["LoggerLike", "SideLogger", "MonoLogger"]


class LoggerLike(Protocol):
    def debug(self, msg: object) -> None:
        pass

    def info(self, msg: object) -> None:
        pass

    def warning(self, msg: object) -> None:
        pass

    def error(self, msg: object) -> None:
        pass

    def critical(self, msg: object) -> None:
        pass

    def exception(self, msg: object) -> None:
        pass


class SideLogger(Thread):
    """### SideLogger: Wraps a logger to log in a separate thread.
    * Use with caution when logging to console."""

    def __init__(self, logger: LoggerLike, heartbeat: float = 0.01) -> None:
        Thread.__init__(self)
        self._heartbeat = heartbeat
        self._queue: Queue = Queue()
        self._logger = logger
        self._subs_lock = Lock()
        self._join_lock = Lock()
        self._subscribers = list[Thread]()

    def _filter_subscribers(self) -> None:
        with self._subs_lock:
            self._subscribers = [s for s in self._subscribers if s.is_alive()]

    def run(self) -> None:
        while True:
            self._filter_subscribers()
            if self._queue.empty():
                if not self._subscribers and self._queue.empty():
                    return  # Double checks for thread safety
                sleep(self._heartbeat)
                continue
            cmd = self._queue.get()
            try:
                match cmd:
                    case (func, args, kw):
                        func(*args, **kw)
                    case -1:
                        return
            finally:
                self._queue.task_done()

    def _log(self, func: Callable[[object], Any], *args, **kw):
        with self._subs_lock:
            thread = current_thread()
            if thread not in self._subscribers:
                self._subscribers.append(thread)
        self._queue.put((func, args, kw))
        if not self.is_alive():
            self.start()

    def debug(self, *args, **kw):
        self._log(self._logger.debug, *args, **kw)

    def info(self, *args, **kw):
        self._log(self._logger.info, *args, **kw)

    def warning(self, *args, **kw):
        self._log(self._logger.warning, *args, **kw)

    def error(self, *args, **kw):
        self._log(self._logger.error, *args, **kw)

    def critical(self, *args, **kw):
        self._log(self._logger.critical, *args, **kw)

    def exception(self, err, *args, **kw):
        if "exc_info" not in kw:
            kw["exc_info"] = err
        self._log(self._logger.exception, err, *args, **kw)

    def join(self, timeout: float = None) -> None:
        """Wait for logger thread to finish. """
        with self._join_lock:
            if self.is_alive():
                self._queue.put(-1)
            if timeout is None:
                self._queue.join()
            else:
                Thread.join(self, timeout)

    @property
    def logger(self) -> LoggerLike:
        return self._logger
