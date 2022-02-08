from .video import VideoUpload, VideoList, VideoGet, VideoDelete
from .timeline import TimelineList, TimelineDuplicate, TimelineDelete, TimelineRename
from .video_analyser import AnalyserList
from .timeline_segment_annotation import TimelineSegmentAnnoatationList, TimelineSegmentAnnoatationCreate
from .timeline_segment import TimelineSegmentList
from .annotation_category import AnnoatationCategoryCreate, AnnoatationCategoryList

from .user import get_csrf_token, login, logout, register, GetUser


# TODO this is not the best way to do it
from backend.tasks import *
