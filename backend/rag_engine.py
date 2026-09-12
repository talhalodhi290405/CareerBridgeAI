import chromadb
from chromadb.utils import embedding_functions
import json
import os

class JobRAG:
    def __init__(self):
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(path="./chroma_db")
        # Use default embedding function
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="job_postings", 
            embedding_function=self.emb_fn
        )

    def index_jobs(self, jobs_path="data/jobs.json"):
        with open(jobs_path, "r") as f:
            jobs = json.load(f)
        
        ids = [j["id"] for j in jobs]
        # Create a search string combining title and description
        documents = [f"{j['title']} - {j['description']}" for j in jobs]
        metadatas = [{"title": j["title"], "company": j["company"], "location": j["location"], "type": j["type"]} for j in jobs]
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"Indexed {len(ids)} jobs into ChromaDB.")

    def search_jobs(self, query, top_k=3):
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Format results for the API
        matches = []
        for i in range(len(results['ids'][0])):
            matches.append({
                "id": results['ids'][0][i],
                "metadata": results['metadatas'][0][i],
                "document": results['documents'][0][i]
            })
        return matches

# Singleton instance
rag_engine = JobRAG()
