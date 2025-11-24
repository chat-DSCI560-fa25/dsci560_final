import chromadb
from chromadb.config import Settings

# Initialize ChromaDB client
chroma_client = chromadb.Client(Settings())
collection = chroma_client.get_or_create_collection(name="lesson_plans")

# Try to get a known document by ID
result = collection.get(ids=["Craftstick Bridge.docx"])
print("Direct ChromaDB get result for 'Craftstick Bridge.docx':")
print(result)
