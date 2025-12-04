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
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/")
    content_text = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    def __str__(self):
        return self.title