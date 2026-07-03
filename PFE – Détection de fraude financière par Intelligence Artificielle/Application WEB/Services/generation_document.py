import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ============================================================
# CONFIGURATION
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHROMA_PATH     = r"C:\Users\Pc\Desktop\crisp-dm\Project_PFE\chroma_db"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
GROQ_API_KEY    = "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"   
GROQ_MODEL      = "llama-3.3-70b-versatile"  
TOP_K           = 5

# ============================================================
# PROMPT TEMPLATE
# ============================================================
PROMPT_TEMPLATE = """
Tu es un assistant expert en détection de transactions suspectes et en concepts bancaires.
Tu réponds UNIQUEMENT en te basant sur le contexte fourni ci-dessous.
Si la réponse n'est pas dans le contexte, dis-le clairement.
Réponds toujours en français, de manière précise et structurée.

CONTEXTE DOCUMENTAIRE :
{context}

HISTORIQUE DE LA CONVERSATION :
{history}

QUESTION ACTUELLE : {question}

RÉPONSE :
"""

# ============================================================
# CHARGEMENT VECTORSTORE
# ============================================================
def load_vectorstore():
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
    logger.info(f"Base chargée : {db._collection.count()} chunks")
    return db

# ============================================================
# GÉNÉRATION DE LA RÉPONSE
# ============================================================
def format_history(history: list) -> str:
    if not history:
        return "Aucun échange précédent."
    lines = []
    for msg in history:
        role    = msg.get("role", "user")
        content = msg.get("content", "").strip()
        if not content:
            continue
        lines.append(f"{'Utilisateur' if role == 'user' else 'Assistant'} : {content}")
    return "\n".join(lines) if lines else "Aucun échange précédent."

def generate(question: str, db, history: list = None) -> str:
    """
    Pipeline RAG avec mémoire conversationnelle :
    1. Retrieval  → chunks pertinents depuis ChromaDB
    2. Historique → injecté dans le prompt
    3. Generation → LLM génère la réponse avec contexte + historique
    """
    if history is None:
        history = []

    # Enrichir la requête de recherche avec le contexte conversationnel
    query_enrichie = question
    if history:
        derniers = [m["content"] for m in history[-2:] if m.get("role") == "user"]
        if derniers:
            query_enrichie = " ".join(derniers) + " " + question

    results = db.similarity_search(query_enrichie, k=TOP_K)

    if not results:
        return "Aucune information trouvée dans la base de connaissances pour cette question."

    context         = "\n\n---\n\n".join([doc.page_content for doc in results])
    history_formate = format_history(history)

    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0.2,
        max_tokens=1024,
        timeout=30,
        max_retries=2,
    )

    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain  = prompt | llm

    try:
        response = chain.invoke({
            "context" : context,
            "history" : history_formate,
            "question": question
        })
        return response.content
    except Exception as e:
        if "rate" in str(e).lower() or "429" in str(e):
            return "⚠️ Limite API atteinte. Attendez quelques secondes et réessayez."
        raise

# ============================================================
# MAIN — TEST
# ============================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  CHATBOT RAG — DÉTECTION TRANSACTIONS SUSPECTES")
    print("="*60)

    db = load_vectorstore()

    questions = [
        "Qu'est-ce qu'une transaction suspecte ?",
        "Comment fonctionne l'Isolation Forest ?",
        "Quels sont les indicateurs d'anomalie bancaire ?",
        "Quelle est la différence entre Label Propagation et Label Spreading ?",
    ]

    for question in questions:
        print(f"\n{'='*60}")
        print(f"Q : {question}")
        print(f"{'='*60}")
        reponse = generate(question, db)
        print(f"R : {reponse}")
        print()