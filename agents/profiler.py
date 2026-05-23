# ============================================================
# PROFILER AGENT — Apprend et mémorise le style de l'utilisateur
# ============================================================

import sqlite3                      # Pour gérer la base de données locale
import json                         # Pour convertir les données en JSON
import os                           # Pour lire les variables d'environnement
from groq import Groq               # Pour appeler le LLM
from dotenv import load_dotenv      # Pour charger le fichier .env
import streamlit as st              # Pour lire les secrets Streamlit

# Charger les variables du fichier .env
load_dotenv()

# Créer le client Groq avec la clé API
client = Groq(api_key=st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY"))


# ============================================================
# FONCTION 1 — Créer la base de données
# ============================================================
def init_db():
    # Utiliser /tmp accessible sur Streamlit Cloud et en local
    data_dir = "/tmp/stylemind_data"                    # Dossier temporaire
    os.makedirs(data_dir, exist_ok=True)                # Créer si inexistant
    db_path = os.path.join(data_dir, "profil.db")       # Chemin complet du fichier DB

    # Connexion à SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Créer la table profil si elle n'existe pas encore
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profil (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            styles TEXT,
            couleurs TEXT,
            budget_min INTEGER,
            budget_max INTEGER,
            taille TEXT,
            marques TEXT,
            occasions TEXT
        )
    """)

    # Sauvegarder et retourner la connexion
    conn.commit()
    return conn


# ============================================================
# FONCTION 2 — Poser des questions à l'utilisateur (terminal)
# ============================================================
def collecter_infos():
    print("\n🎨 Bienvenue dans StyleMind !\n")

    # Chaque input() attend la réponse de l'utilisateur
    style     = input("Ton style ? (ex: casual, chic, streetwear) : ")
    couleurs  = input("Tes couleurs préférées ? (ex: noir, beige) : ")
    budget    = input("Ton budget par article ? (ex: 20-80) : ")
    taille    = input("Ta taille ? (ex: S, M, L, 38, 40) : ")
    marques   = input("Tes marques ? (ex: Zara, Nike, aucune) : ")
    occasions = input("Pour quelles occasions ? (ex: soirée, sport) : ")

    # Regrouper toutes les réponses dans un dictionnaire
    infos = {
        "style"    : style,
        "couleurs" : couleurs,
        "budget"   : budget,
        "taille"   : taille,
        "marques"  : marques,
        "occasions": occasions
    }

    return infos


# ============================================================
# FONCTION 3 — Envoyer les infos au LLM pour les structurer
# ============================================================
def analyser_profil(infos):
    # Construire le prompt pour le LLM
    prompt = f"""
Tu es un expert en mode. Analyse ces préférences et retourne UN JSON structuré.

Préférences :
- Style : {infos['style']}
- Couleurs : {infos['couleurs']}
- Budget : {infos['budget']}
- Taille : {infos['taille']}
- Marques : {infos['marques']}
- Occasions : {infos['occasions']}

Retourne UNIQUEMENT ce JSON, sans texte autour, sans markdown, sans backticks :
{{
    "styles": ["liste", "des", "styles"],
    "couleurs": ["liste", "des", "couleurs"],
    "budget_min": 0,
    "budget_max": 0,
    "taille": "taille",
    "marques": ["liste", "des", "marques"],
    "occasions": ["liste", "des", "occasions"]
}}
"""

    # Appeler Groq avec le modèle actuel
    reponse = client.chat.completions.create(
        model="llama-3.3-70b-versatile",    # Modèle actuel Groq
        messages=[{"role": "user", "content": prompt}]
    )

    # Extraire le texte brut de la réponse
    texte = reponse.choices[0].message.content

    # Nettoyer le texte — supprimer les backticks markdown si présents
    texte = texte.strip()                        # Supprimer espaces début/fin
    texte = texte.replace("```json", "")         # Supprimer ```json
    texte = texte.replace("```", "")             # Supprimer ```
    texte = texte.strip()                        # Nettoyer à nouveau

    # Convertir le JSON texte en dictionnaire Python
    profil_structure = json.loads(texte)

    return profil_structure


# ============================================================
# FONCTION 4 — Sauvegarder le profil dans SQLite
# ============================================================
def sauvegarder_profil(conn, profil):
    cursor = conn.cursor()

    # Insérer le profil — json.dumps() convertit les listes en texte
    cursor.execute("""
        INSERT INTO profil (styles, couleurs, budget_min, budget_max, taille, marques, occasions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        json.dumps(profil["styles"]),       # Convertir liste en texte JSON
        json.dumps(profil["couleurs"]),     # Convertir liste en texte JSON
        profil["budget_min"],               # Entier direct
        profil["budget_max"],               # Entier direct
        profil["taille"],                   # Texte direct
        json.dumps(profil["marques"]),      # Convertir liste en texte JSON
        json.dumps(profil["occasions"])     # Convertir liste en texte JSON
    ))

    conn.commit()
    print("\n✅ Profil sauvegardé !")


# ============================================================
# FONCTION 5 — Charger le dernier profil sauvegardé
# ============================================================
def charger_profil(conn):
    cursor = conn.cursor()

    # Récupérer le profil le plus récent
    cursor.execute("SELECT * FROM profil ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()

    # Si aucun profil trouvé retourner None
    if row is None:
        return None

    # Reconstruire le dictionnaire depuis la base
    profil = {
        "id"        : row[0],
        "styles"    : json.loads(row[1]),
        "couleurs"  : json.loads(row[2]),
        "budget_min": row[3],
        "budget_max": row[4],
        "taille"    : row[5],
        "marques"   : json.loads(row[6]),
        "occasions" : json.loads(row[7])
    }

    return profil


# ============================================================
# POINT D'ENTRÉE — Lancer le Profiler Agent (terminal)
# ============================================================
def run():
    # Étape 1 — Initialiser la base
    conn = init_db()

    # Étape 2 — Collecter les infos
    infos = collecter_infos()

    # Étape 3 — Analyser avec le LLM
    profil = analyser_profil(infos)

    # Étape 4 — Sauvegarder
    sauvegarder_profil(conn, profil)

    # Étape 5 — Afficher le résultat
    print("\n📋 Ton profil style :")
    print(json.dumps(profil, indent=2, ensure_ascii=False))

    # Retourner connexion et profil pour les autres agents
    return conn, profil