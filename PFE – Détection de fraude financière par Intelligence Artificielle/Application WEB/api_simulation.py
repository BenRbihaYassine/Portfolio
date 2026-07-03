"""
api_simulation.py
=================
Blueprint Flask pour la détection de transactions suspectes.

Deux modes de prédiction :
  1. Modèle Random Forest (si model/random_forest.pkl + model/scaler.pkl existent)
  2. Règles métier (fallback) — 6 scénarios suspects issus du PFE

Structure attendue des fichiers modèle :
  model/random_forest.pkl   ← RandomForestClassifier entraîné
  model/scaler.pkl          ← StandardScaler ajusté sur les mêmes features
  model/features.pkl        ← liste Python des features_final utilisées à l'entraînement
"""

import os
import pickle
import joblib
import numpy as np
import pandas as pd
from flask import Blueprint, request, jsonify

sim_bp = Blueprint("simulation", __name__)

# ── Chemins modèle ──────────────────────────────────────────────────────────
_BASE = os.path.dirname(__file__)
MODEL_PATH = os.path.join(_BASE, "model", "xgboost.pkl")
SCALER_PATH   = os.path.join(_BASE, "model", "scaler.pkl")
FEATURES_PATH = os.path.join(_BASE, "model", "features.pkl")

# ── Liste complète des features (ordre du notebook Feature_engineering) ─────
# Correspondent aux colonnes de features_comptes.xlsx (hors compte/lieu_principal/anomalie)
ALL_FEATURES = [
    "nb_transactions", "total_montant", "montant_moyen", "montant_median",
    "montant_std", "montant_min", "montant_max", "duree_activite_jours",
    "ratio_max_moyen", "nb_transactions_mois", "pct_nocturne", "pct_weekend",
    "nb_lieux_differents", "pct_lieu_principal", "changements_lieu_frequents",
    "temps_moyen_entre_tx_min", "temps_median_entre_tx_min", "temps_min_entre_tx_min",
    "temps_std_entre_tx_min", "montants_croissants_consecutifs", "ratio_montant_max_min",
    "velocite_maximale_km_h", "nb_tpe_moins_100", "ratio_tpe_moins_100", "tx_par_jour",
]

# ── Distances réelles entre gouvernorats tunisiens (km) ─────────────────────
_DIST_BASE = {
    ("Tunis", "Ariana"): 15, ("Tunis", "Ben Arous"): 20, ("Tunis", "Manouba"): 10,
    ("Tunis", "Nabeul"): 65, ("Tunis", "Zaghouan"): 60, ("Tunis", "Bizerte"): 65,
    ("Tunis", "Béja"): 105, ("Tunis", "Jendouba"): 155, ("Tunis", "Le Kef"): 175,
    ("Tunis", "Siliana"): 125, ("Tunis", "Sousse"): 140, ("Tunis", "Monastir"): 160,
    ("Tunis", "Mahdia"): 200, ("Tunis", "Sfax"): 270, ("Tunis", "Kairouan"): 160,
    ("Tunis", "Kasserine"): 300, ("Tunis", "Sidi Bouzid"): 265, ("Tunis", "Gabès"): 405,
    ("Tunis", "Médenine"): 480, ("Tunis", "Tataouine"): 520, ("Tunis", "Gafsa"): 340,
    ("Tunis", "Tozeur"): 430, ("Tunis", "Kébili"): 490,
    ("Ariana", "Ben Arous"): 25, ("Ariana", "Manouba"): 12, ("Ariana", "Nabeul"): 70,
    ("Ariana", "Zaghouan"): 65, ("Ariana", "Bizerte"): 60, ("Ariana", "Béja"): 110,
    ("Ariana", "Jendouba"): 160, ("Ariana", "Le Kef"): 180, ("Ariana", "Siliana"): 130,
    ("Ariana", "Sousse"): 145, ("Ariana", "Monastir"): 165, ("Ariana", "Mahdia"): 205,
    ("Ariana", "Sfax"): 275, ("Ariana", "Kairouan"): 165, ("Ariana", "Kasserine"): 305,
    ("Ariana", "Sidi Bouzid"): 270, ("Ariana", "Gabès"): 410, ("Ariana", "Médenine"): 485,
    ("Ariana", "Tataouine"): 525, ("Ariana", "Gafsa"): 345, ("Ariana", "Tozeur"): 435,
    ("Ariana", "Kébili"): 495,
    ("Ben Arous", "Manouba"): 18, ("Ben Arous", "Nabeul"): 55, ("Ben Arous", "Zaghouan"): 50,
    ("Ben Arous", "Bizerte"): 75, ("Ben Arous", "Béja"): 115, ("Ben Arous", "Jendouba"): 165,
    ("Ben Arous", "Le Kef"): 185, ("Ben Arous", "Siliana"): 135, ("Ben Arous", "Sousse"): 135,
    ("Ben Arous", "Monastir"): 155, ("Ben Arous", "Mahdia"): 195, ("Ben Arous", "Sfax"): 265,
    ("Ben Arous", "Kairouan"): 155, ("Ben Arous", "Kasserine"): 295,
    ("Ben Arous", "Sidi Bouzid"): 260, ("Ben Arous", "Gabès"): 400,
    ("Ben Arous", "Médenine"): 475, ("Ben Arous", "Tataouine"): 515,
    ("Ben Arous", "Gafsa"): 335, ("Ben Arous", "Tozeur"): 425, ("Ben Arous", "Kébili"): 485,
    ("Nabeul", "Sousse"): 90, ("Nabeul", "Monastir"): 110, ("Nabeul", "Mahdia"): 150,
    ("Nabeul", "Sfax"): 220, ("Nabeul", "Kairouan"): 130, ("Sousse", "Monastir"): 20,
    ("Sousse", "Mahdia"): 60, ("Sousse", "Sfax"): 130, ("Sousse", "Kairouan"): 55,
    ("Sousse", "Kasserine"): 175, ("Monastir", "Mahdia"): 40, ("Monastir", "Sfax"): 110,
    ("Sfax", "Gabès"): 135, ("Sfax", "Gafsa"): 130, ("Gabès", "Médenine"): 80,
    ("Gabès", "Tataouine"): 120, ("Médenine", "Tataouine"): 50,
    ("Gafsa", "Tozeur"): 95, ("Gafsa", "Kébili"): 130, ("Tozeur", "Kébili"): 90,
    ("Kasserine", "Sidi Bouzid"): 75, ("Kasserine", "Gafsa"): 110,
    ("Sidi Bouzid", "Sfax"): 100, ("Kairouan", "Sidi Bouzid"): 100,
    ("Béja", "Jendouba"): 50, ("Béja", "Le Kef"): 70, ("Bizerte", "Béja"): 60,
    ("Jendouba", "Le Kef"): 60, ("Le Kef", "Siliana"): 70, ("Siliana", "Kairouan"): 50,
}
DISTANCES = {}
for (v1, v2), d in _DIST_BASE.items():
    DISTANCES[(v1, v2)] = d
    DISTANCES[(v2, v1)] = d


# ── Chargement du modèle (lazy, une seule fois) ──────────────────────────────
_model   = None
_scaler  = None
_features_final = None
_model_loaded   = False


def _load_artifacts():
    """Charge RF + scaler + features une seule fois au premier appel."""
    global _model, _scaler, _features_final, _model_loaded
    if _model_loaded:
        return

    _model_loaded = True  # même si ça échoue, on n'essaie qu'une fois

    def _load(path):
        if not os.path.exists(path):
            return None
        try:
            return joblib.load(path)
        except Exception:
            try:
                with open(path, "rb") as f:
                    return pickle.load(f)
            except Exception:
                return None

    _model          = _load(MODEL_PATH)
    _scaler         = _load(SCALER_PATH)
    _features_final = _load(FEATURES_PATH)

    # Si features.pkl absent, on utilise toutes les features par défaut
    if _features_final is None:
        _features_final = ALL_FEATURES


# ── Calcul des features à partir des transactions brutes ─────────────────────

def aggregate_features(transactions: list) -> dict:
    """
    Calcule les 25 features agrégées par compte,
    identiques au notebook Feature_engineering_2_f.ipynb.
    """
    df = pd.DataFrame(transactions)
    df["montant"]        = pd.to_numeric(df.get("montant", 0), errors="coerce").fillna(0)
    df["date_operation"] = pd.to_datetime(df.get("date_operation"), errors="coerce")
    df["heure"]          = df["date_operation"].dt.hour
    df["jour_semaine"]   = df["date_operation"].dt.dayofweek
    df["mois"]           = df["date_operation"].dt.to_period("M")
    df["Lieu"]           = df.get("lieu", pd.Series(["Autres"] * len(df))).fillna("Autres")
    df["motif_operation"]= df.get("motif", pd.Series([""] * len(df))).fillna("")
    df["sens"]           = df.get("sens", pd.Series(["D"] * len(df))).fillna("D")
    df["weekend"]        = df["jour_semaine"].isin([5, 6])
    df["nocturne"]       = (df["heure"] >= 22) | (df["heure"] < 6)
    df = df.sort_values("date_operation").reset_index(drop=True)

    n       = len(df)
    montants = df["montant"].values
    dates    = df["date_operation"].dropna()

    # Durée activité
    duree_jours = max((dates.max() - dates.min()).days + 1, 1) if len(dates) > 1 else 1

    # Transactions par mois (moyenne)
    tx_par_mois = df.groupby("mois").size().mean() if df["mois"].nunique() > 0 else float(n)

    # Temporel
    pct_nocturne = float(df["nocturne"].mean())
    pct_weekend  = float(df["weekend"].mean())

    # Géographique
    lieux = df["Lieu"].tolist()
    nb_lieux_differents = df["Lieu"].nunique()
    lieu_counts     = df["Lieu"].value_counts()
    lieu_principal  = lieu_counts.index[0]
    pct_lieu_principal = lieu_counts.iloc[0] / n

    if n > 1:
        changements = sum(1 for i in range(1, n) if lieux[i] != lieux[i - 1])
        changements_lieu_frequents = changements / n
    else:
        changements_lieu_frequents = 0.0

    # Temps entre transactions (minutes)
    if len(dates) > 1:
        diffs_min = [
            (dates.iloc[i + 1] - dates.iloc[i]).total_seconds() / 60
            for i in range(len(dates) - 1)
        ]
    else:
        diffs_min = [0.0]

    temps_moyen  = float(np.mean(diffs_min))
    temps_median = float(np.median(diffs_min))
    temps_min    = float(np.min(diffs_min))
    temps_std    = float(np.std(diffs_min)) if len(diffs_min) > 1 else 0.0

    # Montants croissants consécutifs (longueur de la plus longue séquence)
    max_croissants = croissants_actuels = 0
    for i in range(n - 1):
        if montants[i + 1] > montants[i]:
            croissants_actuels += 1
            max_croissants = max(max_croissants, croissants_actuels)
        else:
            croissants_actuels = 0

    # Ratio max/min montant
    montant_min = float(np.min(montants))
    montant_max = float(np.max(montants))
    ratio_montant_max_min = montant_max / montant_min if montant_min > 0 else montant_max

    # Vélocité maximale (km/h)
    velocite_max = 0.0
    for i in range(n - 1):
        lieu1, lieu2 = lieux[i], lieux[i + 1]
        if lieu1 == lieu2:
            continue
        distance = DISTANCES.get((lieu1, lieu2), 0)
        if distance == 0:
            continue
        delta_min = diffs_min[i] if i < len(diffs_min) else 0
        if delta_min <= 0:
            velocite_max = 99999.0  # Même instant, lieux différents = physiquement impossible
        else:
            velocite_max = max(velocite_max, distance / (delta_min / 60))

    # TPE < 100 DT (motif commence par 'T' ET montant < 100)
    tpe_mask       = df["motif_operation"].str.startswith("T", na=False) & (df["montant"] < 100)
    nb_tpe         = int(tpe_mask.sum())
    ratio_tpe      = nb_tpe / n

    # Transactions par jour actif
    nb_jours_actifs = max(df["date_operation"].dt.date.nunique(), 1)
    tx_par_jour     = n / nb_jours_actifs

    # Stats montant
    montant_std    = float(np.std(montants)) if n > 1 else 0.0
    montant_moyen  = float(np.mean(montants))
    montant_median = float(np.median(montants))
    ratio_max_moyen = montant_max / max(montant_moyen, 0.01)

    return {
        "nb_transactions":              n,
        "total_montant":                float(np.sum(montants)),
        "montant_moyen":                montant_moyen,
        "montant_median":               montant_median,
        "montant_std":                  montant_std,
        "montant_min":                  montant_min,
        "montant_max":                  montant_max,
        "duree_activite_jours":         duree_jours,
        "ratio_max_moyen":              ratio_max_moyen,
        "nb_transactions_mois":         tx_par_mois,
        "pct_nocturne":                 pct_nocturne,
        "pct_weekend":                  pct_weekend,
        "nb_lieux_differents":          nb_lieux_differents,
        "pct_lieu_principal":           pct_lieu_principal,
        "changements_lieu_frequents":   changements_lieu_frequents,
        "temps_moyen_entre_tx_min":     temps_moyen,
        "temps_median_entre_tx_min":    temps_median,
        "temps_min_entre_tx_min":       temps_min,
        "temps_std_entre_tx_min":       temps_std,
        "montants_croissants_consecutifs": max_croissants,
        "ratio_montant_max_min":        ratio_montant_max_min,
        "velocite_maximale_km_h":       velocite_max,
        "nb_tpe_moins_100":             nb_tpe,
        "ratio_tpe_moins_100":          ratio_tpe,
        "tx_par_jour":                  tx_par_jour,
        # extra (non-features mais utile pour les règles)
        "_lieux":    lieux,
        "_montants": montants.tolist(),
        "_nocturnes": df["nocturne"].tolist(),
        "_sens":      df["sens"].tolist(),
        "_n":         n,
    }


# ── Règles métier (6 scénarios PFE) ──────────────────────────────────────────

def _apply_business_rules(f: dict) -> tuple[str, float, list[str]]:
    """
    Applique les 6 scénarios suspects définis dans le PFE.
    Retourne (statut, confidence, [raisons]).

    Scénarios :
      S1 — Petits montants suivis d'un retrait important
      S2 — Succession rapide de montants croissants
      S3 — Transactions répétées de faibles montants à intervalles réduits
      S4 — Opérations débit/crédit de montants similaires (smurfing)
      S5 — Retraits dans des localisations différentes en peu de temps (vélocité)
      S6 — Passage d'une activité diurne à des transactions nocturnes inhabituelles
    """
    raisons   = []
    scores    = []

    n        = f["_n"]
    montants = f["_montants"]
    lieux    = f["_lieux"]
    nocturnes= f["_nocturnes"]
    sens     = f["_sens"]

    # ── S1 : Petits montants suivis d'un retrait important ───────────────────
    # Définition : au moins 3 transactions < 200 DT suivies d'un montant > 5× la moyenne
    if n >= 4:
        petits  = [m for m in montants[:-1] if m < 200]
        dernier = montants[-1]
        moy_petits = np.mean(petits) if petits else 0
        if len(petits) >= 2 and dernier > max(5 * moy_petits, 500):
            raisons.append(
                f"S1 — Petits montants ({len(petits)} tx < 200 DT, moy={moy_petits:.0f} DT) "
                f"suivis d'un retrait important ({dernier:.0f} DT)"
            )
            scores.append(0.85)

    # ── S2 : Succession rapide de montants croissants ────────────────────────
    # Définition : séquence croissante ≥ 3 transactions consécutives ET
    #              temps médian entre elles ≤ 60 min
    if f["montants_croissants_consecutifs"] >= 3 and f["temps_median_entre_tx_min"] <= 60:
        raisons.append(
            f"S2 — Succession rapide de montants croissants "
            f"({f['montants_croissants_consecutifs']} tx consécutives, "
            f"intervalle médian={f['temps_median_entre_tx_min']:.1f} min)"
        )
        scores.append(0.80)

    # ── S3 : Transactions répétées de faibles montants à intervalles réduits ─
    # Définition : ≥ 4 transactions, montant moyen < 150 DT ET
    #              temps min entre tx ≤ 5 min (rafale)
    if (n >= 4
            and f["montant_moyen"] < 150
            and f["temps_min_entre_tx_min"] <= 5
            and f["tx_par_jour"] >= 4):
        raisons.append(
            f"S3 — Rafale de petits paiements répétés "
            f"(moy={f['montant_moyen']:.0f} DT, intervalle min={f['temps_min_entre_tx_min']:.1f} min, "
            f"{f['tx_par_jour']:.1f} tx/jour)"
        )
        scores.append(0.82)

    # ── S4 : Opérations débit/crédit de montants similaires ──────────────────
    # Définition : au moins 1 paire (débit, crédit) avec écart ≤ 5 % du montant
    if n >= 2 and "D" in sens and "C" in sens:
        debits  = [montants[i] for i in range(n) if sens[i] == "D"]
        credits = [montants[i] for i in range(n) if sens[i] == "C"]
        paires_suspectes = 0
        for d in debits:
            for c in credits:
                if d > 0 and abs(d - c) / d <= 0.05:
                    paires_suspectes += 1
        if paires_suspectes >= 1:
            raisons.append(
                f"S4 — {paires_suspectes} paire(s) débit/crédit de montants identiques "
                f"(écart ≤ 5 %)"
            )
            scores.append(0.78)

    # ── S5 : Retraits dans localisations différentes en peu de temps ─────────
    # Définition : vélocité > 200 km/h OU situation géographiquement impossible
    if f["velocite_maximale_km_h"] >= 99999:
        raisons.append(
            "S5 — Transactions simultanées dans des lieux différents "
            "(géographiquement impossible — usurpation ou clonage de carte probable)"
        )
        scores.append(0.97)
    elif f["velocite_maximale_km_h"] > 200:
        raisons.append(
            f"S5 — Vélocité géographique suspecte : {f['velocite_maximale_km_h']:.0f} km/h "
            f"entre {f['nb_lieux_differents']} lieu(x) différent(s)"
        )
        scores.append(0.88)

    # ── S6 : Passage d'activité diurne → transactions nocturnes inhabituelles ─
    # Définition : pct_nocturne > 60 % ET au moins 3 transactions
    #              (si peu de données, seuil abaissé à 80 %)
    seuil_nuit = 0.60 if n >= 5 else 0.80
    if f["pct_nocturne"] > seuil_nuit and n >= 3:
        raisons.append(
            f"S6 — Activité majoritairement nocturne inhabituellement élevée "
            f"({f['pct_nocturne']*100:.0f} % des transactions entre 22h et 6h)"
        )
        scores.append(0.75)

    # ── Décision finale ───────────────────────────────────────────────────────
    if raisons:
        # Confiance = score le plus élevé parmi les règles déclenchées
        confidence = max(scores)
        statut     = "Suspect"
    else:
        statut     = "Normal"
        # Confiance basée sur l'absence d'indicateurs à risque
        # Si quelques indicateurs modérés → confiance plus basse
        risque_partiel = (
            f["pct_nocturne"] > 0.35
            or f["nb_lieux_differents"] > 3
            or f["ratio_max_moyen"] > 5
        )
        confidence = 0.72 if risque_partiel else 0.88

    return statut, confidence, raisons


# ── Endpoint principal ───────────────────────────────────────────────────────

@sim_bp.route("/api/predict", methods=["POST"])
def predict():
    data         = request.get_json(force=True)
    transactions = data.get("transactions", [])

    if not transactions:
        return jsonify({"error": "Aucune transaction fournie"}), 400

    # ── 1. Calcul des features ───────────────────────────────────────────────
    features = aggregate_features(transactions)

    # Indicateurs à renvoyer au frontend
    indicateurs = {
        k: round(v, 3) if isinstance(v, float) else v
        for k, v in features.items()
        if k in [
            "pct_nocturne", "pct_weekend", "velocite_maximale_km_h",
            "ratio_tpe_moins_100", "montant_moyen", "nb_lieux_differents",
            "tx_par_jour", "ratio_montant_max_min",
        ]
    }

    # ── 2. Essai avec le modèle XGboost ────────────────────────────────
    _load_artifacts()

    note  = ""
    raisons = []

    if _model is not None and _scaler is not None:
        try:
            feats_used = _features_final if _features_final else ALL_FEATURES
            X_row = {f: features.get(f, 0) for f in feats_used}
            X     = pd.DataFrame([X_row])[feats_used]
            X_sc  = _scaler.transform(X)

            pred  = _model.predict(X_sc)[0]
            proba = _model.predict_proba(X_sc)[0]

            statut     = "Suspect" if pred == 1 else "Normal"
            confidence = float(max(proba))
            note = "Prédiction XGBoost (modèle supervisé)"

            # Enrichissement : même si le XGboost dit Normal, on vérifie les règles
            # pour fournir des justifications lisibles
            _, _, raisons = _apply_business_rules(features)

            # Si le XGboost dit Normal mais des règles critiques (S1/S5) sont déclenchées,
            # on respecte le modèle ML mais on signale les anomalies en "avertissement"
            if statut == "Normal" and raisons:
                note += " — indicateurs à surveiller détectés"

        except Exception as e:
            # Chute sur les règles métier si le modèle plante
            statut, confidence, raisons = _apply_business_rules(features)
            note = f"Règles métier (erreur modèle : {str(e)[:60]})"
    else:
        # ── 3. Fallback : règles métier ──────────────────────────────────────
        statut, confidence, raisons = _apply_business_rules(features)
        note = "Prédiction par règles métier (modèle non chargé)"

    return jsonify({
        "compte":     transactions[0].get("compte", "—"),
        "statut":     statut,
        "confidence": round(confidence * 100, 1),
        "note":       note,
        "nb_tx":      features["nb_transactions"],
        "raisons":    raisons,          # liste des scénarios suspects déclenchés
        "indicateurs": indicateurs,
    })