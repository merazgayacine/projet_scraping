# Projet Algorithmique Python - Sujet 2

Master 1 IdL - Semestre 2 - 2025/2026  
Groupe de 2 etudiants

---

## Description

Ce projet consiste a constituer un corpus d'articles de presse par web scraping depuis le site France Info, puis a classifier ces articles par categorie avec un modele Transformer.

Le projet se divise en deux parties :

- **Partie 1** : collecte automatique d'articles de presse avec leurs categories (labels) via web scraping
- **Partie 2** : classification supervisee des articles avec un modele Transformer (CamemBERT)

---

## Structure des fichiers

```
projet_scraping/
    web_scraping.py       # script de collecte des donnees (Partie 1)
    web_scraping.ipynb    # notebook avec explications (Partie 1)
    classification.py     # script de classification (Partie 2)
    articles.csv          # dataset genere par le scraping
    requirements.txt      # dependances Python
    readme.md             # ce fichier
```

---

## Installation

### 1. Cloner le depot

```bash
git clone <url_du_depot>
cd projet_scraping
```

### 2. Creer un environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dependances

```bash
pip install -r requirements.txt
```

---

## Utilisation

### Partie 1 : Web Scraping

Lancer le script de scraping :

```bash
python3 web_scraping.py
```

Ou ouvrir le notebook :

```bash
jupyter notebook web_scraping.ipynb
```

Le script va collecter 10 articles par categorie depuis France Info et sauvegarder le resultat dans `articles.csv`.

### Partie 2 : Classification

```bash
python3 classification.py
```

---

## Source de donnees

Site : France Info (https://www.francetvinfo.fr)

Le fichier robots.txt du site autorise le scraping des articles sous User-agent: *. Les sections utilisees ne figurent pas dans la liste Disallow.

Sections scrapees :

| Label | URL |
|---|---|
| politique | francetvinfo.fr/politique/ |
| sport | francetvinfo.fr/sports/ |
| economie | francetvinfo.fr/economie/ |
| sante | francetvinfo.fr/sante/ |
| sciences | francetvinfo.fr/sciences/ |

---

## Format du dataset

Le fichier `articles.csv` contient 3 colonnes :

| Colonne | Type | Description |
|---|---|---|
| url | str | adresse de l'article |
| texte | str | contenu textuel de l'article |
| label | str | categorie de l'article |

Exemple :

```
url,texte,label
https://www.francetvinfo.fr/politique/article1.html,"Le gouvernement a annonce...",politique
https://www.francetvinfo.fr/sports/article2.html,"Le PSG a gagne...",sport
```

---

## Statistiques du dataset

- Total articles : 50
- Categories : 5 (politique, sport, economie, sante, sciences)
- Articles par categorie : 10

---

## Description des fonctions

### scraper_section(url_section, label, nb_articles)

Recupere les articles d'une section France Info.

- Entree : url_section (str), label (str), nb_articles (int, defaut=10)
- Sortie : liste de dicts {url, texte, label}

### sauvegarder_csv(donnees, nom_fichier)

Sauvegarde la liste d'articles dans un fichier CSV.

- Entree : donnees (list), nom_fichier (str)
- Sortie : fichier CSV cree ou mis a jour sur le disque

### afficher_statistiques(nom_fichier)

Affiche les statistiques du dataset.

- Entree : nom_fichier (str)
- Sortie : affichage dans le terminal

---

## Gestion des erreurs

- Timeout : si le site ne repond pas en 10 secondes, l'article est ignore
- Erreur HTTP : si le code de reponse est 4xx ou 5xx, l'article est ignore
- Article trop court : si le texte fait moins de 300 caracteres, il est ignore
- Doublons : chaque URL est visitee une seule fois
- Pause : une pause d'1 seconde est respectee entre chaque requete

---

## Dependances

| Bibliotheque | Usage |
|---|---|
| requests | envoi des requetes HTTP |
| lxml | analyse du HTML |
| csv | sauvegarde en CSV |
| time | pauses entre requetes |
| os | gestion des fichiers |
| pandas | manipulation du dataset |

---

## Technologies utilisees

- Python 3.12
- requests
- lxml
- pandas
- transformers (Partie 2)
- PyTorch (Partie 2)
