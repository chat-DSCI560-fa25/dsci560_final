"""
Lesson Plan Indexing Script
Extracts text from lesson plan files and stores embeddings in ChromaDB for semantic search.
"""

import os
from glob import glob
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from pdfminer.high_level import extract_text as extract_pdf_text
from docx import Document

LESSON_PLAN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Lesson Plans'))

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="chromadb_data")
collection = chroma_client.get_or_create_collection(name="lesson_plans")

# Load embedding model
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def extract_text_from_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf':
        try:
            return extract_pdf_text(filepath)
        except Exception as e:
            return f"[PDF extraction error: {e}]"
    elif ext in ['.docx', '.doc']:  # Only .docx supported
        try:
            doc = Document(filepath)
            return '\n'.join([p.text for p in doc.paragraphs])
        except Exception as e:
            return f"[DOCX extraction error: {e}]"
    elif ext in ['.txt', '.md']:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"[Text extraction error: {e}]"
    else:
        return os.path.basename(filepath)


def extract_metadata_from_filename(filename):
    # Example: "Grade7_Biology_Photosynthesis.docx" → grade: 7, subject: Biology, topic: Photosynthesis
    name = os.path.splitext(filename)[0]
    parts = name.replace('-', '_').replace(' ', '_').split('_')
    meta = {}
    for part in parts:
        if part.lower().startswith('grade') and part[5:].isdigit():
            meta['grade'] = int(part[5:])
        elif part.lower() in ['biology', 'chemistry', 'physics', 'math', 'science', 'english', 'history']:
            meta['subject'] = part
        else:
            if 'topic' not in meta:
                meta['topic'] = part
    return meta

def index_lesson_plans():
    files = glob(os.path.join(LESSON_PLAN_DIR, '*'))
    for f in files:
        text = extract_text_from_file(f)
        print(f"Extracted text from {os.path.basename(f)}: {text[:300].replace(chr(10), ' ')}\n---")
        embedding = embedder.encode(text)
        filename = os.path.basename(f)
        meta = extract_metadata_from_filename(filename)
        # Add snippet preview
        snippet = text[:200].replace('\n', ' ')
        metadata = {"filename": filename, "snippet": snippet, **meta}
        collection.add(
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
            ids=[filename]
        )
        print(f"Indexed: {filename} | Meta: {metadata}")

if __name__ == "__main__":
    index_lesson_plans()
    print("Lesson plan indexing complete.")
