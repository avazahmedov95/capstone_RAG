import os
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from ingestion.ingest import extract_pages, chunk_pages


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INDEX_DIR = BASE_DIR / "vectorstore" / "faiss_index"

def build_faiss(chunks, embeddings, save_path):
    if not chunks:
        raise ValueError("No text chunks found. Check PDF extraction and chunking.")

    texts = [c["text"] for c in chunks]
    metadata = [c["metadata"] for c in chunks]

    if not texts:
        raise ValueError("No texts to embed.")

    vectorstore = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadata
    )

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    vectorstore.save_local(save_path)


if __name__ == "__main__":
    all_chunks = []
    print("DATA_DIR:", DATA_DIR)
    print("PDF files:", list(DATA_DIR.glob("*.pdf")))
    for pdf in Path(DATA_DIR).glob("*.pdf"):
        print(f"📄 Processing {pdf.name}")
        pages = extract_pages(str(pdf))
        chunks = chunk_pages(pages)
        all_chunks.extend(chunks)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    build_faiss(all_chunks, embeddings, INDEX_DIR)

    print("FAISS index created successfully")
