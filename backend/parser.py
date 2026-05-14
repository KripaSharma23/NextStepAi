import pypdf
import io

def parse_pdf(file_bytes: bytes) -> str:
    """
    Takes raw PDF bytes, returns extracted text as a string.
    """
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    
    return full_text.strip()