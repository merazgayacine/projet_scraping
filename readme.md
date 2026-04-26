# Projet Web Scraping + Classification NLP
**Master 1 IdL — Algorithmique Python S2 — 2025/2026**  
**Groupe** : Yacine Merazga  
**Sujet 2** : Projet dirigé — Web scraping + Classification supervisée Transformer

---

## Description

Projet en deux parties :

**Partie 1** : Constitution d'un corpus par web scraping de France Info (francetvinfo.fr), 50 articles répartis en 5 catégories déjà labellisées par le site (politique, sport, économie, santé, sciences).

**Partie 2** : Classification supervisée des articles avec le modèle CamemBERT (camembert-base, HuggingFace Transformers), en suivant le tutoriel officiel : https://huggingface.co/docs/transformers/tasks/sequence_classification

---

## Installation et dépendances

### Prérequis

- Python 3.10+
- pip
- Connexion internet

### Installation locale (Partie 1)

```bash
git clone https://github.com/merazgayacine/projet_scraping_classification.git
cd projet_scraping_classification

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Dépendances — Partie 1

```
requests
lxml
pandas
```

### Dépendances — Partie 2

```
transformers
torch
datasets
scikit-learn
pandas
```

> **Note** : La Partie 2 nécessite un GPU. Utiliser Google Colab (GPU T4 gratuit).

### Utilisation

```bash
# Partie 1 : générer le corpus
source venv/bin/activate
python3 web_scraping.py
# Génère articles.csv

# Partie 2 : classification
# Ouvrir classification.ipynb sur Google Colab
# Uploader articles.csv
# Exécuter toutes les cellules
```

---

## Organisation des fichiers

```
projet_scraping_classification/
├── web_scraping.py          # Script scraping complet (Partie 1)
├── web_scraping.ipynb       # Notebook Partie 1 avec explications
├── classification.ipynb     # Notebook Partie 2 CamemBERT (Colab)
├── articles.csv             # Dataset généré (50 articles)
├── requirements.txt         # Dépendances Python
└── readme.md                # Ce fichier (cahier des charges + API)
```

---

## Source des données

**Site** : France Info — francetvinfo.fr  
**Robots.txt** : sections autorisées sous `User-agent: *`

| Catégorie | URL scrapée |
|-----------|-------------|
| politique | francetvinfo.fr/politique/ |
| sport | francetvinfo.fr/sports/ |
| economie | francetvinfo.fr/economie/ |
| sante | francetvinfo.fr/sante/ |
| sciences | francetvinfo.fr/sciences/ |

Les labels sont extraits directement depuis l'URL des articles — aucune annotation manuelle.

---

## Statistiques et propriétés du dataset

| Propriété | Valeur |
|-----------|--------|
| Nombre total d'articles | 50 |
| Nombre de catégories | 5 |
| Articles par catégorie | 10 |
| Longueur moyenne des textes | ~2 000 caractères |
| Longueur minimale (filtrée) | 300 caractères |
| Format | CSV UTF-8, 6 colonnes |
| Split train/test | 80% / 20% (40 train, 10 test) |

**Colonnes du CSV** :

| Colonne | Type | Description |
|---------|------|-------------|
| url | str | URL complète de l'article |
| titre | str | Titre extrait de la balise h1 |
| date | str | Date de publication (datetime ISO) |
| chapeau | str | Meta description de la page |
| texte | str | Corps de l'article (balise article) |
| label | str | Catégorie : politique/sport/economie/sante/sciences |

---

## Mini-cahier des charges — API

### Partie 1 : web_scraping.py

---

#### `extraire_label_depuis_url(url)`

**Fonctionnalité** : Extrait la catégorie d'un article directement depuis son URL, sans avoir à analyser le contenu HTML.

**Entrée** :
- `url` (str) : URL complète de l'article (ex: `https://www.francetvinfo.fr/politique/article.html`)

**Sortie** :
- `label` (str) : catégorie de l'article (`politique`, `sport`, `economie`, `sante`, `sciences`)
- `None` si aucun label trouvé

**Complexité** : O(k) — k = nombre de catégories (5), constant

**Exemple** :
```python
extraire_label_depuis_url("https://www.francetvinfo.fr/politique/article.html")
# → "politique"
```

---

#### `extraire_metadonnees(tree, url)`

**Fonctionnalité** : Extrait les métadonnées structurées d'un article (titre, date, chapeau, label) depuis l'arbre HTML parsé.

**Entrée** :
- `tree` (lxml.html.HtmlElement) : arbre DOM de la page parsée par lxml
- `url` (str) : URL de l'article pour extraction du label

**Sortie** :
- `dict` : `{titre: str, date: str, chapeau: str, label: str}`

**Structures de données** :
- Entrée : arbre DOM (structure arborescente)
- Sortie : dictionnaire Python clé→valeur

**Complexité** : O(n) — n = nombre de nœuds HTML parcourus par XPath

---

#### `extraire_texte_article(tree)`

**Fonctionnalité** : Extrait uniquement le texte du corps de l'article en ciblant la balise `<article>`, évitant ainsi les menus, newsletters et vidéos répétés sur chaque page.

**Problème résolu** : L'extraction naïve `//p//text()` récupérait tout le contenu de la page (menus, newsletters, listes de vidéos) identique sur chaque article. La correction `//article//p//text()` cible uniquement le corps éditorial.

**Stratégie en cascade** :
1. `//article//p//text()` — cas standard (balise `<article>`)
2. `//*[contains(@class,'article/content/body')]//p//text()` — fallback classes CSS
3. `//p//text()` — dernier recours

**Entrée** :
- `tree` (lxml.html.HtmlElement) : arbre DOM de la page article

**Sortie** :
- `texte` (str) : texte propre, lignes < 20 caractères filtrées

**Complexité** : O(n) — n = nombre de nœuds HTML

**Pseudo-code** :
```
paragraphes <- xpath("//article//p//text()")
SI vide: paragraphes <- xpath("//div[@class='article']//p//text()")
SI vide: paragraphes <- xpath("//p//text()")
POUR chaque ligne:
    SI len(ligne) > 20: garder
RETOURNER jointure(lignes_gardees)
```

---

#### `scraper_section(url_section, label, nb_articles=10)`

**Fonctionnalité** : Récupère `nb_articles` articles d'une section France Info. Visite la page de section, collecte les liens d'articles, puis scrappe chaque article individuellement avec un délai de 1 seconde entre chaque requête.

**Entrée** :
- `url_section` (str) : URL de la section (ex: `https://www.francetvinfo.fr/politique/`)
- `label` (str) : catégorie associée
- `nb_articles` (int) : nombre d'articles à récupérer (défaut : 10)

**Sortie** :
- `list[dict]` : liste de dictionnaires `{url, titre, date, chapeau, texte, label}`

**Structures de données** :
- `urls_visitees` : ensemble (set) pour éviter les doublons — O(1) en moyenne pour la recherche
- `resultats` : liste de dictionnaires, ajout en O(1)

**Gestion des exceptions** :
- `requests.exceptions.Timeout` : timeout réseau
- `requests.exceptions.HTTPError` : erreur HTTP (404, 403...)
- `requests.exceptions.RequestException` : erreur réseau générale

**Complexité** : O(nb_articles × T_réseau) — T_réseau = temps d'une requête HTTP

---

#### `sauvegarder_csv(donnees, nom_fichier)`

**Fonctionnalité** : Sauvegarde les articles dans un fichier CSV en mode append (ajout). Crée l'en-tête si le fichier n'existe pas.

**Entrée** :
- `donnees` (list[dict]) : liste d'articles
- `nom_fichier` (str) : chemin du fichier CSV

**Sortie** : fichier CSV écrit sur le disque (encodage UTF-8)

**Structure de données** : liste de dictionnaires → CSV (format tabulaire)

**Complexité** : O(n) — n = nombre d'articles

---

#### `afficher_statistiques(nom_fichier)`

**Fonctionnalité** : Lit le CSV et affiche les statistiques du dataset (total articles, répartition par label, longueur moyenne des textes).

**Entrée** :
- `nom_fichier` (str) : chemin du fichier CSV

**Sortie** : affichage terminal

**Complexité** : O(n) — n = nombre de lignes du CSV

---

### Partie 2 : classification.ipynb

---

#### Pipeline de classification

```
articles.csv
    ↓ pandas.read_csv()
DataFrame (50 lignes, 6 colonnes)
    ↓ LabelEncoder.fit_transform()
label_id : list[int]   (economie=0, politique=1, sante=2, sciences=3, sport=4)
    ↓ train_test_split(test_size=0.2, stratify=y)
X_train (40), X_test (10)
    ↓ CamembertTokenizer(max_length=128, padding, truncation)
{input_ids: Tensor(N,128), attention_mask: Tensor(N,128)}
    ↓ CamembertForSequenceClassification(num_labels=5)
logits : Tensor(batch_size, 5)
    ↓ argmax(axis=1)
predictions : list[int]
    ↓ LabelEncoder.inverse_transform()
labels prédits : list[str]
```

---

#### Structures de données — Partie 2

| Étape | Structure | Type Python | Description |
|-------|-----------|-------------|-------------|
| Chargement CSV | DataFrame | pandas.DataFrame | 50 lignes × 6 colonnes |
| Labels encodés | Vecteur entiers | list[int] | economie=0, politique=1, sante=2, sciences=3, sport=4 |
| Texte tokenisé | Dict tenseurs | dict | {input_ids, attention_mask} |
| input_ids | Tenseur | torch.Tensor(N, 128) | Indices des tokens dans le vocabulaire CamemBERT |
| attention_mask | Tenseur | torch.Tensor(N, 128) | 1 = token réel, 0 = padding |
| Sortie modèle | Logits | torch.Tensor(batch, 5) | Score brut pour chaque classe |
| Prédiction finale | Entier | int → str | argmax(logits) puis LabelEncoder.inverse_transform() |

---

#### `ArticleDataset` (classe)

**Fonctionnalité** : Dataset PyTorch encapsulant les articles tokenisés et leurs labels pour l'entraînement.

**Entrée constructeur** :
- `textes` (list[str]) : textes des articles
- `labels` (list[int]) : labels encodés
- `tokenizer` : tokenizer CamemBERT
- `max_length` (int) : longueur max tokens (défaut : 128)

**Méthodes** :
- `__len__()` → int : nombre d'exemples
- `__getitem__(idx)` → dict : `{input_ids, attention_mask, labels}` pour l'exemple idx

---

#### `compute_metrics(eval_pred)`

**Fonctionnalité** : Calcule accuracy et F1-score pondéré à partir des logits et labels vrais.

**Entrée** :
- `eval_pred` (tuple) : `(logits: np.array(N,5), labels: np.array(N,))`

**Sortie** :
- `dict` : `{accuracy: float, f1: float}`

**Processus** : `logits → argmax(axis=1) → predictions → accuracy_score + f1_score`

---

#### `predire(texte)`

**Fonctionnalité** : Prédit la catégorie d'un nouveau texte avec le modèle entraîné.

**Entrée** :
- `texte` (str) : article ou phrase à classifier

**Sortie** :
- `label` (str) : catégorie prédite

**Pipeline interne** :
```
texte (str)
→ tokenizer(max_length=128)       : {input_ids: Tensor(1,128), attention_mask: Tensor(1,128)}
→ CamemBERT forward pass          : logits Tensor(1, 5)
→ argmax(logits)                  : indice (int)
→ LabelEncoder.inverse_transform  : label (str)
```

---

## Tests et BUGUES identifiés

### Tests effectués

| Test | Résultat |
|------|----------|
| Scraping section politique (10 articles) | OK |
| Scraping section sport (10 articles) | OK |
| Scraping section économie (10 articles) | OK |
| Scraping section santé (10 articles) | OK |
| Scraping section sciences (10 articles) | OK |
| Génération CSV 50 articles | OK |
| Tokenisation CamemBERT | OK |
| Entraînement 3 epochs Colab | OK |
| Prédiction nouveaux textes | OK |

### BUGUES identifiés et corrigés

**BUG 1 — Duplication du texte** (CORRIGÉ)

- **Description** : Le texte extrait contenait les menus de navigation, les listes de vidéos recommandées et les blocs newsletter, identiques sur chaque article. Le contenu utile représentait moins de 20% du texte total.
- **Cause** : XPath `//p//text()` extrait tous les paragraphes de la page sans distinction.
- **Correction** : Remplacement par `//article//p//text()` qui cible uniquement la balise `<article>` contenant le corps éditorial.
- **Impact sur l'analyse** : sans cette correction, le modèle de classification aurait appris sur du bruit (contenu identique entre articles), faussant complètement les résultats.

**BUG 2 — Articles trop courts** (CORRIGÉ)

- **Description** : Certains liens mènent à des pages sans texte d'article (pages de direct, pages de profil), générant des entrées vides dans le CSV.
- **Correction** : Filtre `len(texte_final) < 300` — les articles trop courts sont ignorés.

**BUG 3 — Quota Google Drive Colab** (CORRIGÉ)

- **Description** : L'entraînement sur Colab sauvegardait les checkpoints sur Google Drive, dépassant le quota.
- **Correction** : `output_dir="/tmp/resultats"` et `save_strategy="no"` dans TrainingArguments.

**BUG 4 — Module non trouvé (venv VSCode)** (CORRIGÉ)

- **Description** : VSCode n'utilisait pas l'environnement virtuel activé dans le terminal.
- **Correction** : Toujours lancer le script depuis le terminal avec `source venv/bin/activate` avant `python3 web_scraping.py`.

### Limites connues

- Le scraping peut être ralenti ou bloqué si France Info modifie sa structure HTML ou son robots.txt.
- Avec seulement 50 articles (10 par classe), les performances du modèle restent limitées. Un corpus plus grand améliorerait la classification.
- Le modèle CamemBERT tronque les textes à 128 tokens — les articles longs sont partiellement analysés.

---

## Gestion du projet

**GitHub** : https://github.com/merazgayacine/projet_scraping_classification

```bash
# Cloner le dépôt
git clone https://github.com/merazgayacine/projet_scraping_classification.git

# Pousser les modifications
git add .
git commit -m "description des changements"
git push origin main
```

---

## Références

- HuggingFace Transformers — Sequence Classification : https://huggingface.co/docs/transformers/tasks/sequence_classification
- CamemBERT : https://huggingface.co/camembert-base
- France Info robots.txt : https://www.francetvinfo.fr/robots.txt
