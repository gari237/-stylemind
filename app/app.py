# ============================================================
# APP — Interface Streamlit de StyleMind
# ============================================================

import streamlit as st          # Pour créer l'interface web
import sys                      # Pour manipuler les chemins Python
import os                       # Pour les variables d'environnement

# Ajouter le dossier racine au path pour importer les agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import profiler     # Importer le Profiler Agent
from agents import scout        # Importer le Scout Agent
from agents import ranker       # Importer le Ranker Agent
from agents import advisor      # Importer l'Advisor Agent

# ============================================================
# CONFIGURATION DE LA PAGE
# ============================================================

# Configurer la page Streamlit
st.set_page_config(
    page_title="StyleMind",         # Titre de l'onglet navigateur
    page_icon="👗",                  # Icône de l'onglet
    layout="centered"               # Centrer le contenu
)

# Titre principal
st.title("👗 StyleMind")
st.subheader("Ton conseiller shopping IA personnalisé")
st.divider()                        # Ligne de séparation


# ============================================================
# FORMULAIRE — Collecter le profil utilisateur
# ============================================================

st.header("🎨 Dis-moi ton style")

# Créer deux colonnes pour le formulaire
col1, col2 = st.columns(2)

with col1:
    # Sélecteur de style
    style = st.selectbox(
        "Ton style",
        ["casual", "chic", "streetwear", "bohème", "sportif", "classique"]
    )

    # Sélecteur de couleurs (plusieurs choix possibles)
    couleurs = st.multiselect(
        "Tes couleurs préférées",
        ["noir", "blanc", "beige", "gris", "bleu", "rouge", "vert", "rose"],
        default=["beige"]           # Valeur par défaut
    )

    # Slider budget
    budget_max = st.slider(
        "Budget maximum par article (€)",
        min_value=10,               # Minimum 10€
        max_value=200,              # Maximum 200€
        value=50,                   # Valeur par défaut
        step=5                      # Pas de 5€
    )

with col2:
    # Champ texte pour la taille
    taille = st.text_input(
        "Ta taille",
        placeholder="ex: S, M, L, 38, 40"
    )

    # Champ texte pour les marques
    marques = st.text_input(
        "Tes marques préférées",
        placeholder="ex: Zara, Nike, H&M"
    )

    # Sélecteur d'occasions (plusieurs choix possibles)
    occasions = st.multiselect(
        "Pour quelles occasions ?",
        ["quotidien", "travail", "soirée", "sport", "voyage", "week-end"],
        default=["quotidien"]       # Valeur par défaut
    )

st.divider()


# ============================================================
# BOUTON — Lancer l'analyse
# ============================================================

# Bouton principal centré
if st.button("✨ Trouver mes articles", type="primary", use_container_width=True):

    # Vérifier que les champs obligatoires sont remplis
    if not taille:
        st.error("⚠️ Indique ta taille pour continuer.")     # Message d'erreur
    elif not couleurs:
        st.error("⚠️ Choisis au moins une couleur.")
    elif not occasions:
        st.error("⚠️ Choisis au moins une occasion.")
    else:
        # Construire le profil manuellement (sans passer par les questions terminal)
        profil = {
            "styles"    : [style],          # Style choisi
            "couleurs"  : couleurs,         # Couleurs sélectionnées
            "budget_min": 0,                # Budget minimum (fixé à 0)
            "budget_max": budget_max,       # Budget maximum du slider
            "taille"    : taille,           # Taille saisie
            "marques"   : [m.strip() for m in marques.split(",")] if marques else ["aucune"],
            "occasions" : occasions         # Occasions sélectionnées
        }

        # Sauvegarder le profil en base de données
        with st.spinner("💾 Sauvegarde du profil..."):
            conn = profiler.init_db()               # Initialiser la base
            profiler.sauvegarder_profil(conn, profil)  # Sauvegarder

        # Lancer le Scout Agent
        with st.spinner("🔍 Recherche de produits en cours..."):
            produits = scout.run(profil)            # Trouver les produits

        # Lancer le Ranker Agent
        with st.spinner("⭐ Analyse et scoring des produits..."):
            produits_scores = ranker.run(produits, profil)   # Scorer les produits

        # Lancer l'Advisor Agent
        with st.spinner("🎯 Génération du conseil personnalisé..."):
            resume = advisor.run(produits_scores, profil)    # Générer le conseil

        st.divider()


        # ============================================================
        # AFFICHAGE — Résultats
        # ============================================================

        st.header("🏆 Tes recommandations")

        # Afficher le conseil de l'Advisor en premier
        st.info(resume["conseil"])

        st.subheader("📦 Classement des produits")

        # Afficher chaque produit dans une carte
        for i, p in enumerate(produits_scores):
            # Couleur de la médaille selon le rang
            if i == 0:
                medaille = "🥇"     # Or pour le premier
            elif i == 1:
                medaille = "🥈"     # Argent pour le deuxième
            elif i == 2:
                medaille = "🥉"     # Bronze pour le troisième
            else:
                medaille = f"{i+1}."  # Numéro pour les autres

            # Créer un expander pour chaque produit (cliquable)
            with st.expander(f"{medaille} {p['nom']} — {p['prix']} | Score : {p.get('score_total', '?')}/10"):
                # Afficher les détails du produit
                col_a, col_b = st.columns(2)

                with col_a:
                    st.metric("Prix", p['prix'])            # Prix
                    st.metric("Marque", p['marque'])        # Marque
                    st.metric("Score total", f"{p.get('score_total', '?')}/10")  # Score

                with col_b:
                    st.metric("Style", f"{p.get('score_style', '?')}/10")        # Score style
                    st.metric("Prix/Budget", f"{p.get('score_prix', '?')}/10")   # Score prix
                    st.metric("Occasion", f"{p.get('score_occasion', '?')}/10")  # Score occasion

                # Justification du score
                st.caption(f"💬 {p.get('justification', '')}")