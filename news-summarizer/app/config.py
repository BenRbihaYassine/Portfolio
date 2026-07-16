import os
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()

class Config:
    # --- API Keys ---
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # --- Modèle LLM ---
    LLM_MODEL = "llama-3.3-70b-versatile"  # modèle Groq utilisé
    LLM_TEMPERATURE = 0.3  # peu de créativité, on veut de la fidélité au texte source

    # --- Paramètres de résumé ---
    SUMMARY_MAX_LENGTH = 150   # nombre de mots max du résumé
    SUMMARY_MIN_LENGTH = 50    # nombre de mots min du résumé

    # --- Chemins des dossiers ---
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
    DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

    # --- Scraping ---
    REQUEST_TIMEOUT = 10  # secondes
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


# Vérification au chargement (utile pour debug)
if not Config.GROQ_API_KEY:
    print("⚠️  ATTENTION : GROQ_API_KEY n'est pas définie dans le fichier .env")