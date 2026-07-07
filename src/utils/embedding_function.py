import os
import json
import chromadb
from pathlib import Path
from src.utils.logger import get_logger
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

logger = get_logger(__name__)

def embedding_function(path_to_db: str, path_to_data: str) -> None:
    try:
        client = chromadb.PersistentClient(path=path_to_db)
        folder_path = Path(path_to_data)
        ef = SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        for file_name in folder_path.iterdir():
            try:
                if not file_name.is_file():
                    continue
                collection = client.get_or_create_collection(Path(file_name).stem, embedding_function=ef)
                
                with open(file_name, "r") as file:
                    datas = json.loads(file.read())
                
                ids = []
                documents = []
                metadatas = []
                
                for data in datas:
                    ids.append(data["id"])
                    documents.append(data["content"])
                    metadatas.append(data["metadata"])
                
                collection.upsert(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"Upserted {len(ids)} records into collection {Path(file_name).stem}")
            except Exception as e:
                logger.error(f"Error processing file {file_name.name}: {e}")

    except Exception as e:
        logger.error(f"Error in Embedding Function : {e}")
    else:
        logger.info("Embedding Function executed successfully.")

if __name__ == "__main__":
    embedding_function("chromadb", "data/processed")
