# ============================================================
# ADVISOR AGENT — Génère une recommandation finale personnalisée
# ============================================================

import json                         # Pour manipuler les données JSON
import os                           # Pour les variables d'environnement
from groq import Groq               # Pour appeler le LLM
from dotenv import load_dotenv      # Pour charger le fichier .env
import streamlit as st              # Pour lire les secrets Streamlit

# Charger les variables d'environnement
load_dotenv()

# Créer le client Groq
client = Groq(api_key=st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY"))


# ============================================================
# FONCTION 1 — Générer le conseil final
# ============================================================
def generer_conseil(produits_scores, profil):
    # Prendre uniquement le top 3 pour le prompt
    top3 = produits_scores[:3]

    # Construire le prompt
    prompt = f"""
Tu es un conseiller shopping mode expert et bienveillant.

Profil de l'utilisateur :
- Style : {profil['styles']}
- Couleurs : {profil['couleurs']}
- Budget max : {profil['budget_max']}€
- Occasions : {profil['occasions']}

Top 3 des produits recommandés (classés par score) :
1. {top3[0]['nom']} — {top3[0]['prix']} — Score : {top3[0].get('score_total', '?')}/10
2. {top3[1]['nom']} — {top3[1]['prix']} — Score : {top3[1].get('score_total', '?')}/10
3. {top3[2]['nom']} — {top3[2]['prix']} — Score : {top3[2].get('score_total', '?')}/10

Génère un conseil shopping personnalisé en français, structuré ainsi :
- 1 phrase d'intro personnalisée selon le profil
- Ton choix principal (produit #1) avec pourquoi c'est le meilleur choix
- 1 alternative intéressante (produit #2 ou #3)
- 1 conseil style concret pour porter ce produit
- 1 avertissement si un produit dépasse le budget ou ne convient pas à l'occasion

Sois direct, chaleureux, et précis. Maximum 150 mots.
"""

    # Appeler le LLM
    reponse = client.chat.completions.create(
        model="llama-3.3-70b-versatile",    # Modèle Groq actuel
        messages=[{"role": "user", "content": prompt}]
    )

    # Extraire le conseil
    conseil = reponse.choices[0].message.content.strip()

    return conseil


# ============================================================
# FONCTION 2 — Générer le résumé JSON final
# ============================================================
def generer_resume(produits_scores, profil, conseil):
    # Construire le résumé complet de la session
    resume = {
        "profil"          : profil,                 # Profil utilisateur
        "nb_produits"     : len(produits_scores),   # Nombre de produits analysés
        "meilleur_produit": produits_scores[0],     # Produit #1
        "top3"            : produits_scores[:3],    # Top 3
        "conseil"         : conseil                 # Conseil de l'Advisor
    }

    return resume


# ============================================================
# POINT D'ENTRÉE — Lancer l'Advisor Agent
# ============================================================
def run(produits_scores, profil):
    print("\n🎯 Advisor Agent — Génération du conseil personnalisé...\n")

    # Étape 1 — Générer le conseil
    conseil = generer_conseil(produits_scores, profil)

    # Étape 2 — Afficher le conseil
    print("=" * 60)
    print("✨ TON CONSEIL SHOPPING PERSONNALISÉ")
    print("=" * 60)
    print(conseil)
    print("=" * 60)

    # Étape 3 — Générer le résumé complet
    resume = generer_resume(produits_scores, profil, conseil)

    # Étape 4 — Construire le chemin absolu vers data/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Dossier racine
    data_dir = os.path.join(base_dir, "data")                               # Dossier data/
    os.makedirs(data_dir, exist_ok=True)                                    # Créer si inexistant
    json_path = os.path.join(data_dir, "derniere_session.json")             # Chemin complet

    # Étape 5 — Sauvegarder le résumé dans un fichier JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(resume, f, indent=2, ensure_ascii=False)                  # Écrire le JSON

    print("\n💾 Session sauvegardée dans data/derniere_session.json")

    # Retourner le résumé
    return resume