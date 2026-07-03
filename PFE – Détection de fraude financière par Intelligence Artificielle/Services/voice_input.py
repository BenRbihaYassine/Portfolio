import json
import queue
import threading
import logging
import sounddevice as sd

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================
VOSK_MODEL_PATH = r"C:\Users\Pc\Desktop\crisp-dm\documents RAG\Project_PFE\model\vosk-model-fr-0.22"
SAMPLE_RATE     = 16000
BLOCK_SIZE      = 8000    # nombre de frames par bloc audio
MAX_SILENCE_SEC = 2.5     # secondes de silence avant arrêt automatique


# ============================================================
# CHARGEMENT DU MODÈLE (une seule fois)
# ============================================================
_vosk_model = None

def get_vosk_model():
   
    global _vosk_model
    if _vosk_model is None:
        try:
            from vosk import Model
            _vosk_model = Model(VOSK_MODEL_PATH)
            logger.info("Modèle Vosk chargé avec succès")
        except Exception as e:
            logger.error(f"Impossible de charger le modèle Vosk : {e}")
            raise RuntimeError(
                "Modèle Vosk introuvable.\n"
                "1. Téléchargez vosk-model-fr-0.22 sur https://alphacephei.com/vosk/models\n"
                "2. Décompressez-le dans le dossier  model/vosk-model-fr-0.22/"
            )
    return _vosk_model


# ============================================================
# FONCTION PRINCIPALE : écoute micro → texte
# ============================================================
def listen_from_microphone(
    max_silence_sec: float = MAX_SILENCE_SEC,
    status_callback=None
) -> str:
    """
    Écoute le microphone avec sounddevice et retourne le texte reconnu par Vosk.

    Paramètres
    ----------
    max_silence_sec : float
        Durée de silence (en secondes) après laquelle l'enregistrement s'arrête.
    status_callback : callable | None
        Fonction appelée avec un message str pour mettre à jour l'interface
        (ex : st.info). Si None, on utilise print().

    Retourne
    --------
    str : le texte reconnu (peut être vide si rien n'est capté)
    """

    from vosk import KaldiRecognizer

    def _status(msg: str):
        if status_callback:
            status_callback(msg)
        else:
            print(msg)

    model      = get_vosk_model()
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)

    _status("🎙️ Écoute en cours... Parlez maintenant !")

    collected_text = []
    silence_frames = 0
    # Nombre de blocs consécutifs silencieux avant arrêt
    silence_limit  = int((SAMPLE_RATE / BLOCK_SIZE) * max_silence_sec)

    # File d'attente pour recevoir les blocs audio depuis le callback
    audio_queue = queue.Queue()

    # ----------------------------------------------------------
    # Callback sounddevice : appelé automatiquement à chaque bloc
    # ----------------------------------------------------------
    def audio_callback(indata, frames, time_info, status):
        if status:
            logger.warning(f"sounddevice status : {status}")
        # Convertir en bytes (int16 little-endian) attendu par Vosk
        audio_queue.put(bytes(indata))

    # ----------------------------------------------------------
    # Ouverture du flux micro avec sounddevice (pas de PyAudio !)
    # ----------------------------------------------------------
    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype="int16",
        channels=1,
        callback=audio_callback
    ):
        while True:
            try:
                data = audio_queue.get(timeout=1.0)
            except queue.Empty:
                # Aucun bloc reçu pendant 1 s → compter comme silence
                silence_frames += 1
                if silence_frames >= silence_limit and collected_text:
                    _status("⏹️ Silence détecté — enregistrement terminé.")
                    break
                continue

            if recognizer.AcceptWaveform(data):
                # Résultat complet (fin de phrase détectée par Vosk)
                result = json.loads(recognizer.Result())
                text   = result.get("text", "").strip()
                if text:
                    collected_text.append(text)
                    silence_frames = 0
                    _status(f"✅ Reconnu : « {text} »")
                else:
                    silence_frames += 1
            else:
                # Résultat partiel (mot en cours de prononciation)
                partial      = json.loads(recognizer.PartialResult())
                partial_text = partial.get("partial", "").strip()
                if partial_text:
                    silence_frames = 0   # quelqu'un parle → reset silence
                else:
                    silence_frames += 1

            # Arrêt automatique après silence prolongé ET au moins un mot capté
            if silence_frames >= silence_limit and collected_text:
                _status("⏹️ Silence détecté — enregistrement terminé.")
                break

    return " ".join(collected_text)


# ============================================================
# VERSION THREAD (pour ne pas bloquer Streamlit)
# ============================================================
def listen_in_thread(
    result_queue: queue.Queue,
    max_silence_sec: float = MAX_SILENCE_SEC,
    status_callback=None
):
    """
    Lance l'écoute dans un thread séparé et place le résultat dans result_queue.

    Utilisation dans Streamlit :
        q = queue.Queue()
        t = listen_in_thread(q, status_callback=st.info)
        t.join()
        text = q.get()
    """
    def _run():
        try:
            text = listen_from_microphone(max_silence_sec, status_callback)
            result_queue.put(text)
        except Exception as e:
            logger.error(f"Erreur reconnaissance vocale : {e}")
            result_queue.put("")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread


# ============================================================
# TEST STANDALONE
# ============================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=" * 50)
    print("  TEST RECONNAISSANCE VOCALE — Vosk + sounddevice")
    print("=" * 50)
    print("Appuyez sur Entrée pour commencer l'écoute...")
    input()


    texte = listen_from_microphone()
    print(f"\n🎯 Texte final reconnu : « {texte} »")