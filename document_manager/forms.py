import os
from django import forms
from .models import Document
from django.core.exceptions import ValidationError


def validate_document_extension(value):

    allowed_extensions = {".pdf", ".doc", ".docx", ".txt",".md"}
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f"Unsupported file type '{ext}'. Allowed types are: PDF, DOC, DOCX, TXT."
        )

def validate_max_file_size(value, max_size_mb=10):
    max_size_bytes = max_size_mb * 1024 * 1024
    if value.size > max_size_bytes:
        raise ValidationError(
            f"File size exceeds {max_size_mb} MB limit."
        )


class DocumentUploadForm(forms.ModelForm):
    
    title = forms.CharField(label="Title",max_length=200,required=True,
                            error_messages={
                                "required": "Title cannot be empty"
                            },
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter a short title"}),
    )
    file = forms.FileField(label="Attachment",required=True,
                            validators=[validate_document_extension,validate_max_file_size],
                            error_messages={
                                "required": "Mappings cannot be empty"
                            },     
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )
    
    class Meta:
        model = Document
        fields = ["title", "file"]
    