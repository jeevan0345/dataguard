from enum import Enum


class NotificationStatus(str, Enum):
    UNREAD = "Unread"
    READ = "Read"
    ARCHIVED = "Archived"