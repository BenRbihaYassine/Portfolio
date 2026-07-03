"""
app.py — Serveur Flask unifié
"""
import os
import logging
from flask import Flask, render_template, request, jsonify
from api_simulation import sim_bp

SALUTATIONS = {"salut", "bonjour", "bonsoir", "hello", "hi", "salam", "coucou", "hey", "bj"}

REPONSE_SALUTATION = (
    "Bonjour ! 👋 Je suis votre assistant spécialisé dans la détection "
    "de transactions suspectes à la BH Bank.\n"
    "Comment puis-je vous aider ?"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.register_blueprint(sim_bp)

#ChromaDB n'est pas chargé au démarrage de Flask — il est chargé au premier appel à /api/chat.
#Une fois chargé, _rag_db reste en mémoire RAM pour tous les appels suivants grâce aux variables globales.

_rag_db     = None
_rag_loaded = False

def _get_rag_db():
    global _rag_db, _rag_loaded # _rag_loaded : indique si le chargement a déjà été fait # rag db : contiendra la base vectorielle une fois chargée
    if _rag_loaded:
        return _rag_db
    _rag_loaded = True
    try:
        from Services.generation_document import load_vectorstore
        _rag_db = load_vectorstore()
        logger.info("ChromaDB chargé ✅")
    except Exception as e:
        logger.error(f"Impossible de charger ChromaDB : {e}")
        _rag_db = None
    return _rag_db

@app.route("/")
def index():      return render_template("index.html")
@app.route("/simulation")
def simulation(): return render_template("simulation.html")
@app.route("/chatbot")
def chatbot():    return render_template("chatbot.html")
@app.route("/dashboard")
def dashboard():  return render_template("dashboard.html")
@app.route("/about")
def about():      return render_template("about.html")

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data     = request.get_json(force=True)
    question = (data.get("question") or "").strip()
    history  = data.get("history", [])

    if not question:
        return jsonify({"erreur": "Question vide"}), 400

    # ✅ Détection salutation — court-circuit avant RAG
    question_lower = question.lower().strip("!?,. ")
    if question_lower in SALUTATIONS:
        return jsonify({"reponse": REPONSE_SALUTATION, "statut": "succès"})

    # Suite normale : RAG + Groq
    db = _get_rag_db()
    if db is None:
        return jsonify({"reponse": "⚠️ Base de connaissances non disponible.", "statut": "erreur"}), 503
    try:
        from Services.generation_document import generate
        reponse = generate(question, db, history=history)
        return jsonify({"reponse": reponse, "statut": "succès"})
    except Exception as e:
        logger.error(f"Erreur RAG : {e}")
        return jsonify({"reponse": f"⚠️ Erreur : {str(e)[:200]}", "statut": "erreur"}), 500

@app.route("/api/voice", methods=["POST"])
def api_voice():
    if "audio" not in request.files:
        return jsonify({"texte": "", "statut": "erreur", "message": "Aucun fichier audio reçu"}), 400

    audio_file = request.files["audio"]
    import tempfile, json, subprocess
#Le navigateur envoie un blob audio via MediaRecorder. Le format (WebM ou OGG) est détecté automatiquement depuis le content_type.
    content_type = audio_file.content_type or "audio/webm"
    suffix_in = ".ogg" if "ogg" in content_type else (".mp4" if "mp4" in content_type else ".webm")

    with tempfile.NamedTemporaryFile(suffix=suffix_in, delete=False) as tmp_in:
        tmp_in_path = tmp_in.name
        audio_file.save(tmp_in_path)

    tmp_out_path = tmp_in_path.replace(suffix_in, ".wav")
#Étape 2 — Vérification de la taille
    try:
        file_size = os.path.getsize(tmp_in_path)
        if file_size < 500:
            return jsonify({"texte": "", "statut": "erreur",
                "message": f"Audio trop court ({file_size} octets). Parlez plus longtemps."}), 400
#Le fichier audio reçu est converti au format WAV 16 kHz mono à l’aide de FFmpeg, afin d’assurer sa compatibilité avec le moteur de reconnaissance vocale.
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_in_path, "-ar", "16000", "-ac", "1", "-f", "wav", tmp_out_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return jsonify({"texte": "", "statut": "erreur",
                "message": f"Conversion ffmpeg échouée : {result.stderr[-150:]}"}), 500

        model_path = os.path.join(os.path.dirname(__file__), "model", "vosk-model-fr-0.22")
        if not os.path.exists(model_path):
            return jsonify({"texte": "", "statut": "erreur",
                "message": "Modèle Vosk introuvable dans model/vosk-model-fr-0.22/"}), 503

        from vosk import Model, KaldiRecognizer
        import wave

        model      = Model(model_path)
        wf         = wave.open(tmp_out_path, "rb")
        recognizer = KaldiRecognizer(model, wf.getframerate())

        texte_final = []
        while True:
            frames = wf.readframes(4000)
            if not frames: break
            if recognizer.AcceptWaveform(frames):
                res = json.loads(recognizer.Result())
                if res.get("text"): texte_final.append(res["text"])

        final_res = json.loads(recognizer.FinalResult())
        if final_res.get("text"): texte_final.append(final_res["text"])
        wf.close()

        texte = " ".join(texte_final).strip()
        if not texte:
            return jsonify({"texte": "", "statut": "erreur",
                "message": "Vosk n'a pas reconnu de parole. Parlez plus fort et clairement."})

        return jsonify({"texte": texte, "statut": "succès"})

    except FileNotFoundError:
        return jsonify({"texte": "", "statut": "erreur",
            "message": "ffmpeg introuvable — installez-le : winget install ffmpeg"}), 503
    except ImportError:
        return jsonify({"texte": "", "statut": "erreur",
            "message": "Vosk non installé → pip install vosk"}), 503
    except Exception as e:
        logger.error(f"Erreur api_voice : {e}")
        return jsonify({"texte": "", "statut": "erreur", "message": str(e)}), 500
    finally:
        for p in [tmp_in_path, tmp_out_path]:
            try: os.unlink(p)
            except: pass

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)