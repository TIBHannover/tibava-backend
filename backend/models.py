import uuid

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


def gen_hash_id():
    return uuid.uuid4().hex


class Video(models.Model):
    hash_id = models.CharField(max_length=256, default=gen_hash_id)
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    license = models.CharField(max_length=256)
    ext = models.CharField(max_length=256)
    date = models.DateTimeField(auto_now_add=True)
    # some extracted meta information
    fps = models.FloatField(blank=True, null=True)
    duration = models.FloatField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)

    def to_dict(self, include_refs_hashes=True, include_refs=False, **kwargs):
        return {
            "name": self.name,
            "license": self.license,
            "hash_id": self.hash_id,
            "ext": self.ext,
            "date": self.date,
            "fps": self.fps,
            "duration": self.duration,
            "height": self.height,
            "width": self.width,
        }


class VideoAnalyse(models.Model):
    hash_id = models.CharField(max_length=256, default=gen_hash_id)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=256)
    results = models.BinaryField(null=True)
    progres = models.FloatField(default=0.0)
    status = models.CharField(
        max_length=2, choices=[("Q", "Queued"), ("R", "Running"), ("D", "Done"), ("E", "Error")], default="U"
    )

    def to_dict(self):
        return {
            "type": self.type,
            "date": self.date,
            "update_date": self.update_date,
            "progres": self.progres,
            "status": self.status,
        }


class Timeline(models.Model):
    hash_id = models.CharField(max_length=256, default=gen_hash_id)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    type = models.CharField(max_length=256, null=True)

    def to_dict(self, include_refs_hashes=True, include_refs=False, **kwargs):
        result = {
            "hash_id": self.hash_id,
            "name": self.name,
            "type": self.type,
        }
        if include_refs_hashes:
            result["timeline_segments"] = [x.hash_id for x in self.timelinesegment_set.all()]
        elif include_refs:
            result["timeline_segments"] = [
                x.to_dict(include_refs_hashes=include_refs_hashes, include_refs=include_refs, **kwargs)
                for x in self.timelinesegment_set.all()
            ]
        return result

    def clone(self, video=None):
        if not video:
            video = self.video
        hash_id = uuid.uuid4().hex
        new_timeline_db = Timeline.objects.create(video=video, hash_id=hash_id, name=self.name, type=self.type)

        for segment in self.timelinesegment_set.all():
            segment.clone(new_timeline_db)

        return new_timeline_db


class AnnotationCategory(models.Model):
    hash_id = models.CharField(max_length=256, default=gen_hash_id)
    name = models.CharField(max_length=256)
    color = models.CharField(max_length=256, null=True)


class Annotation(models.Model):
    hash_id = models.CharField(max_length=256, default=gen_hash_id)
    category = models.ForeignKey(AnnotationCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    color = models.CharField(max_length=256, null=True)


class TimelineSegment(models.Model):
    hash_id = models.CharField(max_length=256, default=gen_hash_id)
    timeline = models.ForeignKey(Timeline, on_delete=models.CASCADE)
    annotations = models.ManyToManyField(Annotation, through="TimelineSegmentAnnotation")
    color = models.CharField(max_length=256, null=True)
    start = models.FloatField(default=0)
    end = models.FloatField(default=0)

    def to_dict(self, include_refs_hashes=True, include_refs=False, **kwargs):
        result = {
            "hash_id": self.hash_id,
            "color": self.color,
            "start": self.start,
            "end": self.end,
        }
        if include_refs_hashes:
            result["annotations"] = [x.hash_id for x in self.annotations.all()]
        elif include_refs:
            result["annotations"] = [x.to_dict() for x in self.annotations.all()]
        return result

    def clone(self, timeline=None):
        if not timeline:
            timeline = self.timeline
        hash_id = uuid.uuid4().hex
        new_timeline_segment_db = TimelineSegment.objects.create(
            timeline=timeline, hash_id=hash_id, color=self.color, start=self.start, end=self.end
        )

        for annotation in self.timelineannotation_set.all():
            annotation.clone(new_timeline_segment_db)

        return new_timeline_segment_db


# This is basically a many to many connection
class TimelineSegmentAnnotation(models.Model):
    hash_id = models.CharField(max_length=256, default=gen_hash_id)
    timeline_segment = models.ForeignKey(TimelineSegment, on_delete=models.CASCADE)
    annotation = models.ForeignKey(Annotation, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def to_dict(self, include_refs_hashes=True, **kwargs):
        result = {
            "hash_id": self.hash_id,
            "date": self.date,
        }
        if include_refs_hashes:
            result["annotations"] = self.annotation.hash_id
            result["timeline_segment"] = self.timeline_segment.hash_id
        return result
