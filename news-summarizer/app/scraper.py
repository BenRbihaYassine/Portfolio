import trafilatura


def scrape_article(url: str) -> dict:
    """
    Extrait le titre et le texte d'un article de presse à partir de son URL.

    Args:
        url: L'URL de l'article à scraper.

    Returns:
        Un dictionnaire avec 'success', 'title', 'text', et 'error' (si échec).
    """
    downloaded = trafilatura.fetch_url(url)

    if downloaded is None:
        return {
            "success": False,
            "title": None,
            "text": None,
            "error": "Impossible de télécharger la page (URL invalide ou site inaccessible)."
        }

    texte = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
    metadata = trafilatura.extract_metadata(downloaded)

    if not texte or len(texte.strip()) < 100:
        return {
            "success": False,
            "title": metadata.title if metadata else None,
            "text": None,
            "error": "Le texte extrait est trop court ou vide. L'article n'a peut-être pas pu être extrait correctement."
        }

    return {
        "success": True,
        "title": metadata.title if metadata else "Titre non trouvé",
        "text": texte,
        "error": None
    }


# Test rapide si on exécute ce fichier directement
if __name__ == "__main__":
    url_test = "https://lapressedefrance.fr/levolution-des-pratiques-documentaires-dans-les-entreprises-francaises/"
    resultat = scrape_article(url_test)

    if resultat["success"]:
        print("TITRE :", resultat["title"])
        print("\nTEXTE (extrait) :\n", resultat["text"][:500])
    else:
        print("ERREUR :", resultat["error"])