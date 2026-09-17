from sentence_transformers import SentenceTransformer
import chromadb

# 1. Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 2. Create ChromaDB client
client = chromadb.Client()

# 3. Create collection
collection = client.create_collection("test_schemes")

# 4. Example scheme chunks
chunks = [
    "This scheme provides financial assistance to eligible individuals who want to establish a small enterprise.",
    "Applicants must satisfy the eligibility requirements specified by the government.",
    "Applications can be submitted through the official application process.",
    "The scheme supports agricultural activities and farming-related development."
]

# 5. Convert chunks into embeddings
embeddings = model.encode(chunks).tolist()

# 6. Store them in ChromaDB
collection.add(
    ids=["1", "2", "3", "4"],
    documents=chunks,
    embeddings=embeddings
)

# 7. User question
question = "I need financial help to start a small business."

# 8. Convert question into embedding
question_embedding = model.encode(question).tolist()

# 9. Search ChromaDB
results = collection.query(
    query_embeddings=[question_embedding],
    n_results=2
)

print("\nRELEVANT CHUNKS:\n")

for document in results["documents"][0]:
    print("-", document)