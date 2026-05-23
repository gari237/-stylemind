# ============================================================
# APP — Interface Streamlit de StyleMind (version améliorée)
# ============================================================

import streamlit as st          # Pour créer l'interface web
import sys                      # Pour manipuler les chemins Python
import os                       # Pour les variables d'environnement
from groq import Groq           # Pour les combinaisons de tenues

# Ajouter le dossier racine au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import profiler     # Profiler Agent
from agents import scout        # Scout Agent
from agents import ranker       # Ranker Agent
from agents import advisor      # Advisor Agent

# ============================================================
# CONFIGURATION PAGE
# ============================================================
st.set_page_config(
    page_title="StyleMind",
    page_icon="👗",
    layout="centered"
)

# Titre
st.title("👗 StyleMind")
st.subheader("Ton conseiller shopping IA personnalisé")
st.divider()

# ============================================================
# SECTION 1 — Infos personnelles
# ============================================================
st.header("👤 Qui es-tu ?")

col1, col2, col3 = st.columns(3)

with col1:
    prenom = st.text_input("Ton prénom", placeholder="ex: Sophie")     # Prénom

with col2:
    age = st.number_input("Ton âge", min_value=15, max_value=80, value=25)  # Âge

with col3:
    sexe = st.selectbox("Genre", ["Femme", "Homme", "Non-binaire"])     # Genre

st.divider()

# ============================================================
# SECTION 2 — Style et préférences
# ============================================================
st.header("🎨 Ton style")

col1, col2 = st.columns(2)

with col1:
    style = st.selectbox(
        "Style vestimentaire",
        ["casual", "chic", "streetwear", "bohème", "sportif", "classique", "minimaliste"]
    )

    couleurs = st.multiselect(
        "Couleurs préférées",
        ["noir", "blanc", "beige", "gris", "bleu marine", "rouge", "vert", "rose", "marron", "bordeaux"],
        default=["beige"]
    )

    budget_max = st.slider(
        "Budget maximum par article (€)",
        min_value=10, max_value=300, value=60, step=5
    )

with col2:
    taille_haut = st.selectbox(
        "Taille haut",
        ["XS", "S", "M", "L", "XL", "XXL"]
    )

    taille_bas = st.selectbox(
        "Taille bas",
        ["34", "36", "38", "40", "42", "44", "46"]
    )

    marques = st.text_input(
        "Marques préférées",
        placeholder="ex: Zara, H&M, Nike"
    )

    occasions = st.multiselect(
        "Pour quelles occasions ?",
        ["quotidien", "travail", "soirée", "sport", "voyage", "week-end", "rendez-vous"],
        default=["quotidien"]
    )

st.divider()

# ============================================================
# BOUTON — Lancer l'analyse
# ============================================================
if st.button("✨ Trouver mes articles et tenues", type="primary", use_container_width=True):

    # Vérifier les champs obligatoires
    if not prenom:
        st.error("⚠️ Indique ton prénom.")
    elif not couleurs:
        st.error("⚠️ Choisis au moins une couleur.")
    elif not occasions:
        st.error("⚠️ Choisis au moins une occasion.")
    else:
        # Construire le profil complet
        profil = {
            "prenom"     : prenom,                  # Prénom
            "age"        : age,                     # Âge
            "sexe"       : sexe,                    # Genre
            "styles"     : [style],                 # Style
            "couleurs"   : couleurs,                # Couleurs
            "budget_min" : 0,                       # Budget min
            "budget_max" : budget_max,              # Budget max
            "taille"     : f"{taille_haut} / {taille_bas}",  # Tailles combinées
            "marques"    : [m.strip() for m in marques.split(",")] if marques else ["aucune"],
            "occasions"  : occasions                # Occasions
        }

        # Sauvegarder le profil
        with st.spinner("💾 Sauvegarde du profil..."):
            conn = profiler.init_db()
            profiler.sauvegarder_profil(conn, profil)

        # Scout Agent
        with st.spinner("🔍 Recherche de produits..."):
            produits = scout.run(profil)

        # Ranker Agent
        with st.spinner("⭐ Analyse des produits..."):
            produits_scores = ranker.run(produits, profil)

        # Advisor Agent
        with st.spinner("🎯 Génération du conseil..."):
            resume = advisor.run(produits_scores, profil)

        # Générer des combinaisons de tenues
        with st.spinner("👗 Création de tes combinaisons de tenues..."):
            client_groq = Groq(api_key=st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY"))

            prompt_tenues = f"""
Tu es un styliste expert. Crée 3 combinaisons de tenues complètes pour {prenom}, {age} ans, {sexe}.

Profil : style {style}, couleurs {couleurs}, budget {budget_max}€ max, occasions {occasions}.

Retourne UNIQUEMENT ce JSON, sans texte autour, sans backticks :
[
    {{
        "nom": "Nom de la tenue",
        "occasion": "Pour quelle occasion",
        "pieces": ["Pièce 1", "Pièce 2", "Pièce 3", "Pièce 4"],
        "conseil_style": "Un conseil pour porter cette tenue",
        "budget_estime": "XX€ - XX€"
    }}
]
"""
            reponse = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",    # Modèle Groq actuel
                messages=[{"role": "user", "content": prompt_tenues}]
            )

            # Nettoyer et parser la réponse
            texte = reponse.choices[0].message.content.strip()
            texte = texte.replace("```json", "").replace("```", "").strip()

            import json
            tenues = json.loads(texte)              # Convertir en liste Python

        st.divider()

        # ============================================================
        # AFFICHAGE — Résultats personnalisés
        # ============================================================

        st.header(f"✨ Bonjour {prenom} ! Voici tes recommandations")

        # Conseil Advisor
        st.info(resume["conseil"])

        # Combinaisons de tenues
        st.subheader("👗 Tes combinaisons de tenues")

        cols = st.columns(3)                        # 3 colonnes pour les tenues

        for i, tenue in enumerate(tenues):
            with cols[i]:
                st.markdown(f"**{tenue['nom']}**")          # Nom de la tenue
                st.caption(f"📍 {tenue['occasion']}")        # Occasion
                st.markdown("**Pièces :**")
                for piece in tenue['pieces']:
                    st.markdown(f"• {piece}")               # Chaque pièce
                st.success(f"💡 {tenue['conseil_style']}")  # Conseil
                st.metric("Budget estimé", tenue['budget_estime'])  # Budget

        st.divider()

        # Classement produits
        st.subheader("🏆 Classement des produits")

        for i, p in enumerate(produits_scores):
            medaille = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."

            with st.expander(f"{medaille} {p['nom']} — {p['prix']} | Score : {p.get('score_total', '?')}/10"):
                col_a, col_b = st.columns(2)

                with col_a:
                    st.metric("Prix", p['prix'])
                    st.metric("Marque", p['marque'])
                    st.metric("Score total", f"{p.get('score_total', '?')}/10")

                with col_b:
                    st.metric("Style", f"{p.get('score_style', '?')}/10")
                    st.metric("Prix/Budget", f"{p.get('score_prix', '?')}/10")
                    st.metric("Occasion", f"{p.get('score_occasion', '?')}/10")

                st.caption(f"💬 {p.get('justification', '')}")