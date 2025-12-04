from django import forms
from .models import Document



class DocumentUploadForm(forms.ModelForm):
    
    title = forms.CharField(label="Title",max_length=200,required=True,
                            error_messages={
                                "required": "Title cannot be empty"
                            },
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter a short title"}),
    )
    file = forms.FileField(label="Attachment",required=True,
                            error_messages={
                                "required": "Mappings cannot be empty"
                            },     
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )
    
    class Meta:
        model = Document
        fields = ["title", "file"]
    