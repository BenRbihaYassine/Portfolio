import os
import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.embeddings import HuggingFaceEmbeddings #envrironnement dans vscode
from langchain_community.vectorstores import Chroma

# ============================================================
# CONFIGURATION LOGGING
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================
PDF_PATH    = r"C:\Users\Pc\Desktop\crisp-dm\Project_PFE\documents\Base_Connaissances_Bancaire_Anomalies.pdf"
CHROMA_PATH = r"C:\Users\Pc\Desktop\crisp-dm\Project_PFE\chroma_db"

# Modèle d'embeddings local (téléchargé automatiquement ~90MB)
# Multilingue → comprend le français et l'arabe
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

CHUNK_SIZE    = 500   # taille de chaque chunk en caractères
CHUNK_OVERLAP = 50    # chevauchement entre chunks consécutifs


# ============================================================
# ÉTAPE 1 : CHARGEMENT DU PDF
# ============================================================
def load_documents(pdf_path: str):
    """Charge le PDF et retourne une liste de Document."""
    logger.info(f"Chargement du PDF : {pdf_path}")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF introuvable : {pdf_path}")

    loader    = PyPDFLoader(pdf_path)
    documents = loader.load()

    logger.info(f"PDF chargé : {len(documents)} pages")
    return documents


# ============================================================
# ÉTAPE 2 : DÉCOUPAGE EN CHUNKS
# ============================================================
def split_documents(documents):
    """
    Découpe les documents en chunks.

    CHUNK_SIZE = 500 :
      - Assez grand pour contenir une idée complète
      - Assez petit pour être précis lors du retrieval

    CHUNK_OVERLAP = 50 :
      - Évite de couper une phrase à la frontière de deux chunks
      - Maintient la continuité du contexte
    """
    logger.info(f"Découpage en chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    chunks = splitter.split_documents(documents)
    logger.info(f"Chunks créés : {len(chunks)}")

    # Afficher un exemple
    print(f"\n--- Exemple chunk ---")
    print(chunks[0].page_content[:200])
    print(f"---------------------\n")

    return chunks


# ============================================================
# ÉTAPE 3 : CRÉATION DES EMBEDDINGS
# ============================================================
def create_embedding_model():
    """
    Charge le modèle d'embeddings HuggingFace.
    Téléchargé automatiquement au premier lancement (~90MB).
    Modèle multilingue → supporte le français.
    """
    logger.info(f"Chargement du modèle d'embeddings : {EMBEDDING_MODEL}")

    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},   # utiliser "cuda" si GPU disponible
        encode_kwargs={"normalize_embeddings": True}
    )

    logger.info("Modèle d'embeddings chargé")
    return embedding_model


# ============================================================
# ÉTAPE 4 : STOCKAGE DANS CHROMADB
# ============================================================
def index_documents(chunks, embedding_model, force_reindex: bool = False):
    """
    Stocke les chunks et leurs embeddings dans ChromaDB.

    force_reindex=True  → supprime l'ancienne collection et réindexe
    force_reindex=False → utilise la collection existante si elle existe
    """
    if force_reindex and os.path.exists(CHROMA_PATH):
        import shutil
        shutil.rmtree(CHROMA_PATH)
        logger.info("Ancienne base ChromaDB supprimée")

    logger.info(f"Indexation dans ChromaDB : {CHROMA_PATH}")

    db = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=CHROMA_PATH,
        collection_name="banque_anomalies",
        collection_metadata={"hnsw:space": "cosine"}
    )

    logger.info("Indexation terminée")
    return db


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  INDEXATION DU DOCUMENT PDF → CHROMADB")
    print("="*60)

    try:
        # 1. Charger le PDF
        documents = load_documents(PDF_PATH)

        # 2. Découper en chunks
        chunks = split_documents(documents)

        # 3. Créer le modèle d'embeddings
        embedding_model = create_embedding_model()

        # 4. Indexer dans ChromaDB
        # force_reindex=True → à mettre True si tu changes le PDF
        db = index_documents(chunks, embedding_model, force_reindex=True)

        print("\n" + "="*60)
        print("  ✅ INDEXATION TERMINÉE AVEC SUCCÈS")
        print(f"  📄 Pages       : {len(documents)}")
        print(f"  🔪 Chunks      : {len(chunks)}")
        print(f"  💾 Base        : {CHROMA_PATH}/")
        print("="*60)

    except Exception as e:
        logger.critical(f"Erreur : {e}")