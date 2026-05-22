# ============================================================
# RANKER AGENT — Score chaque produit selon le profil utilisateur
# ============================================================

import json                         # Pour manipuler les données JSON
import os                           # Pour les variables d'environnement
from groq import Groq               # Pour appeler le LLM
from dotenv import load_dotenv      # Pour charger le fichier .env

# Charger les variables d'environnement
load_dotenv()

# Créer le client Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ============================================================
# FONCTION 1 — Scorer un produit selon le profil
# ============================================================
def scorer_produit(produit, profil):
    # Construire le prompt d'évaluation pour le LLM
    prompt = f"""
Tu es un expert en mode et en recommandation personnalisée.

Profil de l'utilisateur :
- Styles : {profil['styles']}
- Couleurs : {profil['couleurs']}
- Budget max : {profil['budget_max']}€
- Taille : {profil['taille']}
- Marques préférées : {profil['marques']}
- Occasions : {profil['occasions']}

Produit à évaluer :
- Nom : {produit['nom']}
- Prix : {produit['prix']}
- Marque : {produit['marque']}

Évalue ce produit sur 3 critères et retourne UNIQUEMENT ce JSON, sans texte autour, sans backticks :
{{
    "score_style": 0,
    "score_prix": 0,
    "score_occasion": 0,
    "score_total": 0,
    "justification": "explication courte en 1 phrase"
}}

Règles de scoring (0-10 pour chaque critère) :
- score_style : le produit correspond-il au style et aux couleurs du profil ?
- score_prix : le prix est-il dans le budget ? (10 = bien en dessous, 5 = pile au budget, 0 = au-dessus)
- score_occasion : le produit convient-il aux occasions du profil ?
- score_total : moyenne des 3 scores arrondie à 1 décimale
"""

    # Appeler le LLM
    reponse = client.chat.completions.create(
        model="llama-3.3-70b-versatile",    # Modèle Groq actuel
        messages=[{"role": "user", "content": prompt}]
    )

    # Extraire et nettoyer la réponse
    texte = reponse.choices[0].message.content.strip()
    texte = texte.replace("```json", "").replace("```", "").strip()

    # Convertir le JSON en dictionnaire Python
    scores = json.loads(texte)

    # Retourner les scores
    return scores


# ============================================================
# FONCTION 2 — Scorer tous les produits et les trier
# ============================================================
def scorer_tous(produits, profil):
    # Liste pour stocker les produits avec leurs scores
    produits_scores = []

    # Scorer chaque produit un par un
    for i, produit in enumerate(produits):
        print(f"  ⚙️ Analyse produit {i+1}/{len(produits)} : {produit['nom'][:40]}...")

        # Appeler la fonction de scoring
        scores = scorer_produit(produit, profil)

        # Fusionner le produit et ses scores dans un seul dictionnaire
        produit_score = {**produit, **scores}

        # Ajouter à la liste
        produits_scores.append(produit_score)

    # Trier les produits par score_total décroissant (meilleur en premier)
    produits_scores.sort(key=lambda x: x.get("score_total", 0), reverse=True)

    return produits_scores


# ============================================================
# POINT D'ENTRÉE — Lancer le Ranker Agent
# ============================================================
def run(produits, profil):
    print("\n⭐ Ranker Agent — Scoring des produits en cours...\n")

    # Scorer et trier tous les produits
    produits_scores = scorer_tous(produits, profil)

    # Afficher le classement final
    print("\n🏆 Classement des produits :\n")
    for i, p in enumerate(produits_scores, 1):
        print(f"{i}. [{p.get('score_total', '?')}/10] {p['nom']} — {p['prix']}")
        print(f"   💬 {p.get('justification', '')}\n")

    # Retourner les produits scorés pour le prochain agent
    return produits_scores