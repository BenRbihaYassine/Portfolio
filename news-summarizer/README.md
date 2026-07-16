# Résumeur Automatique d'Articles de Presse en Français

## Description
Application web permettant de résumer automatiquement des articles 
de presse en français en utilisant le modèle de langage LLaMA 3.3-70b 
via l'API Groq.

---
##  Description des modules
### `app/scraper.py` — Extraction des articles
Ce module est responsable de la récupération du contenu brut des articles 
de presse. À partir d'une URL fournie par l'utilisateur, il extrait 
automatiquement le titre, le texte principal et la date de publication 
de l'article en utilisant la librairie `newspaper3k` combinée à 
`BeautifulSoup`. Il gère également les cas d'erreur (URL invalide, 
article inaccessible, contenu vide).

### `app/summarizer.py` — Génération du résumé
Ce module constitue le cœur du projet. Il reçoit le texte brut extrait 
par le scraper et le transmet au modèle de langage LLaMA 3.3-70b via 
l'API Groq. Un prompt structuré est construit pour guider le modèle à 
produire un résumé en français, clair et concis, de la longueur souhaitée 
par l'utilisateur (court, moyen ou long). Le module gère également 
les textes trop longs en les découpant en chunks avant de les envoyer 
au modèle.

### `app/utils.py` — Fonctions utilitaires
Ce module regroupe les fonctions transversales utilisées par les autres 
modules, notamment le nettoyage du texte brut (suppression des caractères 
spéciaux, des espaces inutiles et du contenu non pertinent), la validation 
des URLs, la détection de la langue de l'article, et la sauvegarde 
des résumés dans le dossier `data/processed/`.

### `app/config.py` — Configuration
Ce module centralise tous les paramètres de configuration du projet : 
les clés API (Groq, NewsAPI), les paramètres du modèle (température, 
longueur maximale), et les options de l'application (longueur des résumés, 
nombre d'articles à récupérer).

### `app.py` — Point d'entrée principal
Fichier principal de l'application Flask. Il définit les routes web 
(accueil, résumé depuis URL, recherche par thème) et orchestre 
les appels entre le scraper, le summarizer et l'interface utilisateur.

