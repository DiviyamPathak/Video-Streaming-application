from django.db import models
from django.conf import settings
import uuid


class Video(models.Model):

    class Status(models.TextChoices):
        UPLOADING = 'uploading', 'Uploading'
        PROCESSING = 'processing', 'Processing'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'

    class Visibility(models.TextChoices):
        PUBLIC = 'public', 'Public'
        UNLISTED = 'unlisted', 'Unlisted'
        PRIVATE = 'private', 'Private'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='videos'
    )

    title = models.CharField(
        max_length=200,
        help_text="Video title displayed to users"
    )

    description = models.TextField(
        blank=True,
        help_text="Video description (supports markdown in frontend)"
    )

    thumbnail = models.ImageField(
        upload_to='thumbnails/',
        null=True,
        blank=True
    )


    original_file = models.FileField(
        upload_to='videos/original/',
        null=True,
        help_text="Original uploaded video file"
    )


    duration = models.DurationField(
        null=True,
        blank=True,
        help_text="Video length (extracted from file)"
    )

    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)

    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Original file size in bytes"
    )


    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADING,
        help_text="Current processing status"
    )
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        help_text="Who can view this video"
    )
    processing_progress = models.IntegerField(
        default=0,
        help_text="Processing completion percentage (0-100)"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error details if status is FAILED"
    )
    comments_count = models.IntegerField(
        default=0,
        help_text="Number of comments (updated via signals)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When video was uploaded"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last modification time"
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When video became publicly available"
    )
    class Meta:
        db_table = 'videos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['visibility', '-published_at']),
        ]

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class VideoQuality(models.Model):

    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name='qualities'
    )

    quality_name = models.CharField(
        max_length=20,
        help_text="Quality label (1080p, 720p, etc.)"
    )

    width = models.IntegerField(help_text="Video width in pixels")
    height = models.IntegerField(help_text="Video height in pixels")

    bitrate = models.CharField(
        max_length=20,
        help_text="Target bitrate for encoding"
    )


    file_path = models.CharField(
        max_length=500,
        help_text="Path to transcoded MP4 file"
    )


    hls_playlist_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to HLS playlist file (.m3u8)"
    )

    file_size = models.BigIntegerField(
        null=True,
        help_text="Transcoded file size in bytes"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'video_qualities'
        unique_together = ['video', 'quality_name']
        indexes = [
            models.Index(fields=['video', 'quality_name']),
        ]

    def __str__(self):
        return f"{self.video.title} - {self.quality_name}"


class Comment(models.Model):
    """
    User Comments on Videos

    Supports:
    - Top-level comments (parent=None)
    - Nested replies (parent=another comment)

    Threading depth: 2 levels (comment -> reply)
    For deeper threading, adjust frontend logic.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    content = models.TextField(
        max_length=1000,
        help_text="Comment content (supports markdown)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(
        default=False,
        help_text="Whether comment has been edited"
    )

    class Meta:
        db_table = 'comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['video', '-created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.video.title}"


class Playlist(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='playlists'
    )

    title = models.CharField(
        max_length=200,
        help_text="Playlist name"
    )

    description = models.TextField(
        blank=True,
        help_text="Playlist description"
    )

    is_public = models.BooleanField(
        default=True,
        help_text="Whether others can view this playlist"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'playlists'
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class PlaylistVideo(models.Model):


    playlist = models.ForeignKey(
        Playlist,
        on_delete=models.CASCADE,
        related_name='playlist_videos'
    )

    video = models.ForeignKey(Video, on_delete=models.CASCADE)

    order = models.IntegerField(
        default=0,
        help_text="Position in playlist (0=first)"
    )

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'playlist_videos'
        ordering = ['order']
        unique_together = ['playlist', 'video']

    def __str__(self):
        return f"{self.video.title} in {self.playlist.title}"


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )


    channel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscribers'
    )

    notifications_enabled = models.BooleanField(
        default=True,
        help_text="Whether to notify subscriber of new uploads"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subscriptions'
        unique_together = ['subscriber', 'channel']
        indexes = [
            models.Index(fields=['subscriber', '-created_at']),
            models.Index(fields=['channel']),
        ]

    def __str__(self):
        return f"{self.subscriber.username} -> {self.channel.username}"
