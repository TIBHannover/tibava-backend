from django.core.management.base import BaseCommand, CommandError
from backend.models import Timeline, TimelineView, Video


class Command(BaseCommand):
    help = "Assigns a timeline view id to all timelines without one"

    def handle(self, *args, **options):
        for video in Video.objects.all():
            unassigned_timelines = []
            for timeline in Timeline.objects.filter(video=video):
                if len(timeline.timelineview_set.all()) == 0:
                    unassigned_timelines.append(timeline)

            if len(unassigned_timelines) > 0:
                # create view
                timeline_view_db = TimelineView.objects.create(name="View", video=video)

            for timeline in unassigned_timelines:
                # assign id of the view to the timeline
                # print(dir(timeline), flush=True)
                timeline_view_db.timelines.add(timeline.id)
                # timeline.timelineview_set.add(timeline_view_db.id)

                self.stdout.write(
                    self.style.SUCCESS(f"Assigned timeline view id {timeline_view_db.id} to {timeline.id}")
                )
