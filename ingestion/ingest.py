import fitz
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter


def extract_pages(pdf_path: str):
    doc = fitz.open(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()

        if text.strip():
            pages.append({
                "text": text,
                "page": page_num + 1,  # human-readable
                "file": Path(pdf_path).name
            })

    return pages

def chunk_pages(pages):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    chunks = []

    for page in pages:
        split_texts = splitter.split_text(page["text"])

        for text in split_texts:
            chunks.append({
                "text": text,
                "metadata": {
                    "file": page["file"],
                    "page": page["page"]
                }
            })

    return chunks
