# ============================================================
# SCOUT AGENT — Cherche des produits mode selon le profil
# ============================================================

import requests                     # Pour faire des requêtes HTTP
from bs4 import BeautifulSoup       # Pour parser le HTML des pages web
import json                         # Pour manipuler les données JSON
import os                           # Pour les variables d'environnement
from groq import Groq               # Pour appeler le LLM
from dotenv import load_dotenv      # Pour charger le fichier .env

# Charger les variables d'environnement
load_dotenv()

# Créer le client Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# En-têtes HTTP pour simuler un vrai navigateur (évite les blocages)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


# ============================================================
# FONCTION 1 — Construire une requête de recherche avec le LLM
# ============================================================
def construire_requete(profil):
    # Demander au LLM de générer une requête Google Shopping optimale
    prompt = f"""
Tu es un expert en recherche de vêtements en ligne.

Voici le profil style d'un utilisateur :
- Styles : {profil['styles']}
- Couleurs : {profil['couleurs']}
- Budget : {profil['budget_min']}€ - {profil['budget_max']}€
- Taille : {profil['taille']}
- Marques : {profil['marques']}
- Occasions : {profil['occasions']}

Génère UNE seule requête de recherche courte et efficace (5-8 mots max) pour trouver des vêtements correspondants.
Réponds UNIQUEMENT avec la requête, sans guillemets, sans explication.
Exemple : veste casual noir Zara homme
"""

    # Appeler le LLM
    reponse = client.chat.completions.create(
        model="llama-3.3-70b-versatile",    # Modèle Groq actuel
        messages=[{"role": "user", "content": prompt}]
    )

    # Extraire et nettoyer la requête générée
    requete = reponse.choices[0].message.content.strip()

    # Afficher la requête pour debug
    print(f"\n🔍 Requête de recherche générée : {requete}")

    return requete


# ============================================================
# FONCTION 2 — Scraper les résultats Google Shopping
# ============================================================
def scraper_produits(requete):
    # Encoder la requête pour l'URL
    requete_encodee = requete.replace(" ", "+")

    # URL Google Shopping
    url = f"https://www.google.com/search?q={requete_encodee}&tbm=shop"

    # Faire la requête HTTP
    reponse = requests.get(url, headers=HEADERS, timeout=10)

    # Parser le HTML avec BeautifulSoup
    soupe = BeautifulSoup(reponse.text, "html.parser")

    # Liste pour stocker les produits trouvés
    produits = []

    # Chercher les blocs produits dans la page Google Shopping
    blocs = soupe.find_all("div", class_="sh-dgr__grid-result")

    # Si Google bloque, on utilise des données de démonstration
    if not blocs:
        print("⚠️ Google Shopping bloqué — utilisation de données de démonstration")
        produits = generer_produits_demo(requete)
        return produits

    # Extraire les infos de chaque produit (max 10)
    for bloc in blocs[:10]:
        # Extraire le nom du produit
        nom_tag = bloc.find("h3")
        nom = nom_tag.text.strip() if nom_tag else "Nom inconnu"

        # Extraire le prix
        prix_tag = bloc.find("span", class_="a8Pemb")
        prix = prix_tag.text.strip() if prix_tag else "Prix inconnu"

        # Extraire la marque/vendeur
        marque_tag = bloc.find("span", class_="aULzUe")
        marque = marque_tag.text.strip() if marque_tag else "Marque inconnue"

        # Ajouter le produit à la liste
        produits.append({
            "nom"   : nom,       # Nom de l'article
            "prix"  : prix,      # Prix affiché
            "marque": marque,    # Marque ou vendeur
            "source": "Google Shopping"  # Origine de la donnée
        })

    return produits


# ============================================================
# FONCTION 3 — Générer des produits de démonstration (fallback)
# ============================================================
def generer_produits_demo(requete):
    # Demander au LLM de générer des produits réalistes pour la démo
    prompt = f"""
Tu es un assistant shopping mode.

Génère une liste de 6 produits de vêtements réalistes pour cette recherche : "{requete}"

Retourne UNIQUEMENT ce JSON, sans texte autour, sans backticks :
[
    {{
        "nom": "Nom du produit",
        "prix": "29.99€",
        "marque": "Nom de la marque",
        "source": "Demo"
    }}
]
"""

    # Appeler le LLM
    reponse = client.chat.completions.create(
        model="llama-3.3-70b-versatile",    # Modèle Groq actuel
        messages=[{"role": "user", "content": prompt}]
    )

    # Extraire et nettoyer la réponse
    texte = reponse.choices[0].message.content.strip()
    texte = texte.replace("```json", "").replace("```", "").strip()

    # Convertir en liste Python
    produits = json.loads(texte)

    return produits


# ============================================================
# POINT D'ENTRÉE — Lancer le Scout Agent
# ============================================================
def run(profil):
    print("\n🛍️ Scout Agent — Recherche de produits en cours...\n")

    # Étape 1 — Construire la requête de recherche avec le LLM
    requete = construire_requete(profil)

    # Étape 2 — Scraper les produits
    produits = scraper_produits(requete)

    # Étape 3 — Afficher les résultats
    print(f"\n📦 {len(produits)} produits trouvés :\n")
    for i, p in enumerate(produits, 1):
        print(f"{i}. {p['nom']} — {p['prix']} ({p['marque']})")

    # Retourner la liste des produits pour le prochain agent
    return produits