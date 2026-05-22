# ============================================================
# MAIN — Point d'entrée principal de StyleMind
# ============================================================

from agents import profiler    # Importer le Profiler Agent
from agents import scout       # Importer le Scout Agent
from agents import ranker      # Importer le Ranker Agent
from agents import advisor     # Importer l'Advisor Agent

# Étape 1 — Profiler Agent
conn, profil = profiler.run()

# Étape 2 — Scout Agent
produits = scout.run(profil)

# Étape 3 — Ranker Agent
produits_scores = ranker.run(produits, profil)

# Étape 4 — Advisor Agent
resume = advisor.run(produits_scores, profil)