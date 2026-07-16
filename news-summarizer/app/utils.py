import re
import os
import json
from datetime import datetime
from urllib.parse import urlparse

from app.config import Config


def is_valid_url(url: str) -> bool:
    """Vérifie qu'une chaîne est une URL valide (schéma http/https + domaine)."""
    try:
        resultat = urlparse(url)
        return all([resultat.scheme in ("http", "https"), resultat.netloc])
    except (ValueError, AttributeError):
        return False


def clean_text(text: str) -> str:
    """Nettoie un texte : espaces/sauts de ligne excessifs, espaces en bord."""
    if not text:
        return ""
    texte = re.sub(r"\n{3,}", "\n\n", text)
    texte = re.sub(r"[ \t]{2,}", " ", texte)
    return texte.strip()


def slugify(text: str, max_length: int = 50) -> str:
    """Transforme un titre en identifiant de fichier sûr."""
    texte = text.lower().strip()
    texte = re.sub(r"[àâä]", "a", texte)
    texte = re.sub(r"[éèêë]", "e", texte)
    texte = re.sub(r"[îï]", "i", texte)
    texte = re.sub(r"[ôö]", "o", texte)
    texte = re.sub(r"[ùûü]", "u", texte)
    texte = re.sub(r"[ç]", "c", texte)
    texte = re.sub(r"[^a-z0-9]+", "-", texte)
    texte = texte.strip("-")
    return texte[:max_length] if texte else "article"


def save_raw_article(url: str, title: str, text: str) -> str:
    """Sauvegarde l'article brut dans data/raw/. Retourne le chemin créé."""
    os.makedirs(Config.DATA_RAW_DIR, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin = os.path.join(Config.DATA_RAW_DIR, f"{horodatage}_{slugify(title)}.json")

    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({
            "url": url, "title": title, "text": text,
            "scraped_at": datetime.now().isoformat(),
        }, f, ensure_ascii=False, indent=2)

    return chemin


def save_processed_summary(url: str, title: str, summary: str, original_length: int, summary_length: int) -> str:
    """Sauvegarde le résumé dans data/processed/. Retourne le chemin créé."""
    os.makedirs(Config.DATA_PROCESSED_DIR, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin = os.path.join(Config.DATA_PROCESSED_DIR, f"{horodatage}_{slugify(title)}.json")

    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({
            "url": url, "title": title, "summary": summary,
            "original_length": original_length, "summary_length": summary_length,
            "summarized_at": datetime.now().isoformat(),
        }, f, ensure_ascii=False, indent=2)

    return chemin


def list_processed_summaries(limit: int = None) -> list:
    """Lit tous les résumés sauvegardés dans data/processed/, du plus récent au plus ancien."""
    dossier = Config.DATA_PROCESSED_DIR
    resumes = []

    if os.path.isdir(dossier):
        for nom in os.listdir(dossier):
            if nom.endswith(".json"):
                chemin = os.path.join(dossier, nom)
                try:
                    with open(chemin, "r", encoding="utf-8") as f:
                        resumes.append(json.load(f))
                except (json.JSONDecodeError, OSError):
                    continue

    resumes.sort(key=lambda x: x.get("summarized_at", ""), reverse=True)
    return resumes[:limit] if limit else resumes