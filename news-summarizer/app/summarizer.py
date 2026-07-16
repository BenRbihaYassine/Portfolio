from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import Config


# --- Initialisation du modèle LLM ---
llm = ChatGroq(
    api_key=Config.GROQ_API_KEY,
    model=Config.LLM_MODEL,
    temperature=Config.LLM_TEMPERATURE,
)

# --- Prompt de résumé ---
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Tu es un assistant expert en journalisme, spécialisé dans le résumé "
     "d'articles de presse en français. Tu produis des résumés clairs, fidèles "
     "au texte source, sans opinion personnelle, et sans invention d'information."),
    ("human",
     "Résume l'article suivant en français, en {min_length} à {max_length} mots maximum. "
     "Le résumé doit capturer les idées principales et rester neutre.\n\n"
     "Article :\n{article_text}\n\n"
     "Résumé :")
])

# --- Chaîne LangChain : prompt -> LLM -> texte brut ---
chain = prompt | llm | StrOutputParser()


def summarize_text(article_text: str) -> dict:
    """
    Génère un résumé en français d'un texte d'article.

    Args:
        article_text: Le texte brut de l'article (issu du scraper).

    Returns:
        Un dictionnaire avec 'success', 'summary', et 'error' (si échec).
    """
    if not article_text or len(article_text.strip()) < 100:
        return {
            "success": False,
            "summary": None,
            "error": "Le texte fourni est trop court pour être résumé."
        }

    try:
        resume = chain.invoke({
            "article_text": article_text,
            "min_length": Config.SUMMARY_MIN_LENGTH,
            "max_length": Config.SUMMARY_MAX_LENGTH,
        })
        return {
            "success": True,
            "summary": resume.strip(),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "summary": None,
            "error": f"Erreur lors de la génération du résumé : {str(e)}"
        }


# --- Test rapide si on exécute ce fichier directement ---
if __name__ == "__main__":
    from app.scraper import scrape_article

    url_test = "https://lapressedefrance.fr/levolution-des-pratiques-documentaires-dans-les-entreprises-francaises/"
    article = scrape_article(url_test)

    if article["success"]:
        print("TITRE :", article["title"])
        resultat = summarize_text(article["text"])
        if resultat["success"]:
            print("\nRÉSUMÉ :\n", resultat["summary"])
        else:
            print("ERREUR RÉSUMÉ :", resultat["error"])
    else:
        print("ERREUR SCRAPING :", article["error"])