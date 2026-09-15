# RexNow — version consultation (déploiement Streamlit Cloud)

Application **en lecture seule**, protégée par mot de passe, à déployer gratuitement
sur **Streamlit Community Cloud** pour la partager par un simple lien à des collègues.
Ils peuvent naviguer dans tous les onglets ; **aucun recalcul, aucune clé, aucune
donnée sensible** (uniquement des sorties déjà calculées dans `data/`).

Conçu par **Anthony Morlet-Lavidalie — Rexecode**.

---

## Contenu de ce dossier (= à mettre dans le dépôt GitHub)
```
streamlit_app.py        ← l'application (lecture seule + mot de passe)
requirements.txt        ← dépendances (streamlit, plotly, pandas, numpy)
.streamlit/config.toml  ← thème aux couleurs Rexecode
data/                   ← sorties pré-calculées (prévisions, backtests, importance)
.gitignore
```
> On ne met **jamais** de mot de passe ni de clé dans le dépôt. Le mot de passe se
> configure dans les *Secrets* de Streamlit Cloud (étape 4).

## Étape 1 — Créer un dépôt GitHub (privé recommandé)
1. Sur https://github.com → **New repository** → nom ex. `rexnow-demo` → **Private** → *Create*.

## Étape 2 — Y déposer les fichiers de ce dossier
**Option simple (sans installer git)** : sur la page du dépôt, *Add file → Upload files*,
puis glisser **tout le contenu de `deploy_cloud/`** (y compris les dossiers `data/` et
`.streamlit/`), et *Commit*.
> Astuce : pour uploader un dossier, glissez-le directement dans la zone d'upload GitHub.

**Option git** (si installé) :
```
cd "C:\projets_claude\projet application prévision\deploy_cloud"
git init && git add . && git commit -m "RexNow consultation"
git branch -M main
git remote add origin https://github.com/<votre-compte>/rexnow-demo.git
git push -u origin main
```

## Étape 3 — Déployer sur Streamlit Cloud
1. https://share.streamlit.io → *Sign in with GitHub* (autoriser l'accès, dépôts privés inclus).
2. **Create app → Deploy a public app from a repo** :
   - Repository : `<votre-compte>/rexnow-demo`
   - Branch : `main`
   - **Main file path : `streamlit_app.py`**
3. Cliquer **Deploy**. Au bout de ~1-2 min, l'app est en ligne à une adresse du type
   `https://rexnow-demo-xxxx.streamlit.app`.

## Étape 4 — Définir le mot de passe (obligatoire)
Dans l'app déployée : menu **⋮ (en haut à droite) → Settings → Secrets**, coller :
```
app_password = "choisissez-un-mot-de-passe"
```
*Save*. L'app redémarre : l'accès est désormais protégé.
> Tant qu'aucun `app_password` n'est défini, l'app affiche un avertissement et reste ouverte.

## Étape 5 — Partager
Transmettez à vos collègues **le lien** + **le mot de passe**. Ils ouvrent le lien,
saisissent le mot de passe, et naviguent librement dans les onglets (lecture seule).

---

## Mettre à jour les chiffres plus tard
Quand le modèle a été recalculé (dans le projet principal), recopiez les sorties
fraîches dans `data/` puis re-committez — Streamlit Cloud redéploie tout seul :
```
horizon_summary.json  nowcast_evolution.json  evolution_h1.json
fullbench_preds.csv   cats_importance.json    meta.json
```
(depuis `..\results\pib\` pour les cinq premiers ; `meta.json` = date du millésime).

## Limites à connaître
- **Hébergement public** : l'app est sur un service externe (Snowflake/Streamlit). Le
  mot de passe limite l'accès mais les données déployées sortent des serveurs Rexecode.
  Pour un usage confidentiel pérenne, privilégier un hébergement **interne** (voie DSI).
- Community Cloud met l'app en veille après inactivité (redémarrage en quelques secondes
  à la visite suivante) et limite le nombre d'apps privées.
