# src/parser.py
from io import BytesIO
from pypdf import PdfReader

def extract_text_from_file(uploaded_file) -> str:
    """Extracts raw text from uploaded .txt or .pdf files."""
    if uploaded_file.name.endswith(".pdf"):
        pdf = PdfReader(BytesIO(uploaded_file.read()))
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        return text.strip()
    else:
        return uploaded_file.read().decode("utf-8").strip()