# 👗 StyleMind — Autonomous Personal Shopping Agent

🚀 **Demo live** : https://stylemind-app.streamlit.app/

Un système multi-agents IA qui apprend ton style, analyse des produits et génère des recommandations personnalisées.

## 🏗️ Architecture
[Profiler Agent] → apprend et mémorise le profil style
[Scout Agent]    → recherche des produits pertinents
[Ranker Agent]   → score chaque produit selon le profil
[Advisor Agent]  → génère un conseil personnalisé final

## 🛠️ Stack technique

| Composant | Technologie |
|-----------|-------------|
| LLM | Groq API — llama-3.3-70b-versatile |
| Orchestration | Python multi-agents (from scratch) |
| Base de données | SQLite |
| UI | Streamlit |
| Scraping | BeautifulSoup + requests |

## 🚀 Lancement local

```bash
pip install -r requirements.txt
streamlit run app/app.py
```

## 📁 Structure
stylemind/
├── agents/
│   ├── profiler.py    # Profil utilisateur + SQLite
│   ├── scout.py       # Recherche produits
│   ├── ranker.py      # Scoring LLM
│   └── advisor.py     # Recommandation finale
├── app/
│   └── app.py         # Interface Streamlit
└── requirements.txt

