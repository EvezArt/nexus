"""
Nexus Capabilities Package — all sidekick capabilities in one importable package.
"""

from .web_scraper import WebScraper, ScrapeResult
from .file_manager import FileManager, FileInfo
from .email_client import EmailClient, Email
from .calendar import Calendar, CalendarEvent
from .code_runner import CodeRunner, ExecutionResult
from .image_gen import ImageGenerator, ImageResult
from .voice import Voice, SpeechResult, TranscriptResult
from .scheduler import TaskScheduler, ScheduledTask, TaskStatus
from .notifications import Notifier, Notification, Priority, Channel
from .plugins import PluginManager, BasePlugin, PluginMeta

__all__ = [
    "WebScraper", "ScrapeResult",
    "FileManager", "FileInfo",
    "EmailClient", "Email",
    "Calendar", "CalendarEvent",
    "CodeRunner", "ExecutionResult",
    "ImageGenerator", "ImageResult",
    "Voice", "SpeechResult", "TranscriptResult",
    "TaskScheduler", "ScheduledTask", "TaskStatus",
    "Notifier", "Notification", "Priority", "Channel",
    "PluginManager", "BasePlugin", "PluginMeta",
]
