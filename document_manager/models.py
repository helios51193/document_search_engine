from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model


class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract=True


# Create your models here.
User = get_user_model()

class Document(TimeStampModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("indexing", "Indexing"),
        ("ready", "Ready"),
        ("error", "Error"),
    ]
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="documents"
    )
    progress = models.PositiveSmallIntegerField(default=0)
    last_indexed_at = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/")
    content_text = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    embedding_model = models.CharField(
        max_length=100,
        blank=True,
        help_text="Embedding model used during last indexing",
    )

    chunk_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of chunks created during last indexing",
    )

    token_count = models.PositiveIntegerField(
        default=0,
        help_text="Approximate token count used for embeddings",
    )
    metadata = models.JSONField(blank=True, null=True, default=dict)
    def __str__(self):
        return self.title

class SiteSetting(models.Model):
    PROVIDER_CHOICES = [
        ("openai", "OpenAI"),
        ("ollama", "Ollama"),
    ]

    key = models.CharField(max_length=100, unique=True)  # e.g. "embedding_provider"
    value = models.CharField(max_length=50, choices=PROVIDER_CHOICES, default="openai")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}={self.value}"

    @classmethod
    def get_provider(cls):
        try:
            s = cls.objects.get(key="embedding_provider")
            return s.value
        except cls.DoesNotExist:
            return "openai"

class Chunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    index = models.IntegerField()  # the nth chunk in the document
    text = models.TextField()
    start_offset = models.IntegerField(null=True, blank=True)
    end_offset = models.IntegerField(null=True, blank=True)
    vector_id = models.CharField(max_length=64, blank=True)  # ID in Qdrant

    class Meta:
        unique_together = ("document", "index")

class SearchLog(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    query = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    num_results = models.IntegerField()
    latency_ms = models.IntegerField()


class SearchEvent(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL, null=True, blank=True)
    query = models.CharField(max_length=300)
    threshold = models.FloatField(default=0.75)
    result_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    top_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.query} ({self.created_at:%Y-%m-%d %H:%M})"