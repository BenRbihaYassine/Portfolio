from flask import Flask, render_template, request

from app.scraper import scrape_article
from app.summarizer import summarize_text
from app.utils import is_valid_url, clean_text, save_raw_article, save_processed_summary, list_processed_summaries

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    resultat = None
    url_soumise = ""

    if request.method == "POST":
        url_soumise = request.form.get("url", "").strip()

        if not url_soumise:
            resultat = {"success": False, "error": "Merci de fournir une URL."}
        elif not is_valid_url(url_soumise):
            resultat = {"success": False, "error": "L'URL n'est pas valide. Vérifie qu'elle commence par http:// ou https://"}
        else:
            article = scrape_article(url_soumise)

            if not article["success"]:
                resultat = {"success": False, "error": article["error"]}
            else:
                texte_propre = clean_text(article["text"])
                save_raw_article(url_soumise, article["title"], texte_propre)

                resume = summarize_text(texte_propre)

                if not resume["success"]:
                    resultat = {"success": False, "error": resume["error"]}
                else:
                    longueur_originale = len(texte_propre.split())
                    longueur_resume = len(resume["summary"].split())
                    compression = round(100 - (longueur_resume / longueur_originale * 100)) if longueur_originale else 0

                    save_processed_summary(url_soumise, article["title"], resume["summary"], longueur_originale, longueur_resume)

                    resultat = {
                        "success": True,
                        "url": url_soumise,
                        "title": article["title"],
                        "summary": resume["summary"],
                        "original_length": longueur_originale,
                        "summary_length": longueur_resume,
                        "compression": compression,
                    }

    return render_template("index.html", resultat=resultat, url_soumise=url_soumise)


@app.route("/historique")
def historique():
    resumes = list_processed_summaries()
    return render_template("historique.html", resumes=resumes)


if __name__ == "__main__":
    app.run(debug=True)