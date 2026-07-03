import logging
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ============================================================
# CONFIGURATION
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHROMA_PATH     = r"C:\Users\Pc\Desktop\crisp-dm\Project_PFE\chroma_db"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K           = 5   # nombre de chunks à récupérer par question


# ============================================================
# CHARGEMENT DE LA BASE CHROMADB
# ============================================================
def load_vectorstore():
    """
    Charge la base ChromaDB déjà indexée.
    Ne recrée pas les embeddings — utilise ceux stockés.
    """
    logger.info("Chargement de la base ChromaDB...")

    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_model,
        collection_name="banque_anomalies"
    )

    logger.info(f"Base chargée : {db._collection.count()} chunks disponibles")
    return db


# ============================================================
# RECHERCHE DES CHUNKS PERTINENTS
# ============================================================
def retrieve(query: str, db, top_k: int = TOP_K):
    """
    Recherche les chunks les plus pertinents pour une question.

    Utilise la similarité cosinus entre :
      - le vecteur de la question
      - les vecteurs des chunks stockés

    Retourne les top_k chunks les plus proches.
    """
    logger.info(f"Recherche pour : '{query}'")

    results = db.similarity_search_with_score(query, k=top_k)

    print(f"\n{'='*60}")
    print(f"Question : {query}")
    print(f"{'='*60}")

    for i, (doc, score) in enumerate(results, 1):
        print(f"\n--- Chunk {i} (score similarité : {score:.4f}) ---")
        print(f"Page source : {doc.metadata.get('page', '?') + 1}")
        print(f"Contenu     : {doc.page_content[:300]}...")

    return [doc for doc, score in results]


# ============================================================
# MAIN — TEST
# ============================================================
if __name__ == "__main__":
    db = load_vectorstore()

    # Questions de test
    questions = [
        "Qu'est-ce qu'une transaction suspecte ?",
        "Comment fonctionne l'Isolation Forest ?",
        "Quels sont les indicateurs d'anomalie bancaire ?",
    ]

    for question in questions:
        chunks = retrieve(question, db)
        print(f"\n✅ {len(chunks)} chunks récupérés\n")