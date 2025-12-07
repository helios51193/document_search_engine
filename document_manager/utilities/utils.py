import os
from PyPDF2 import PdfReader
from docx import Document as DocxDocument


def extract_text_from_file(path):
    
    ext = os.path.splitext(path)[1].lower()

    if ext == ".txt" or ext == '.md':
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    
    if ext == ".pdf":
        reader = PdfReader(path)
        parts = []
        for page in reader.pages:
            text = page.extract_text() or ""
            parts.append(text)
        return "\n".join(parts)

    if ext == ".docx":
        doc = DocxDocument(path)
        parts = [p.text for p in doc.paragraphs]
        return "\n".join(parts)

    raise ValueError("Unsupported file format for text extraction")
    
    
