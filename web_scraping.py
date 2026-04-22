import requests
from lxml import html
import csv
import time
import os

# Sections a scraper avec leurs labels
SECTIONS = {
    "politique": "https://www.francetvinfo.fr/politique/",
    "sport":     "https://www.francetvinfo.fr/sports/",
    "economie":  "https://www.francetvinfo.fr/economie/",
    "sante":     "https://www.francetvinfo.fr/sante/",
    "sciences":  "https://www.francetvinfo.fr/sciences/",
}

NB_ARTICLES = 10
FICHIER_CSV = "articles.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def scraper_section(url_section, label, nb_articles=10):
    """
    Recupere les articles d'une section France Info.
    Entree : url_section (str), label (str), nb_articles (int)
    Sortie : liste de dicts {"url", "texte", "label"}
    """
    resultats = []

    try:
        reponse = requests.get(url_section, headers=HEADERS, timeout=10)
        reponse.raise_for_status()
    except requests.exceptions.Timeout:
        print("Erreur : timeout sur la section " + label)
        return resultats
    except requests.exceptions.HTTPError as e:
        print("Erreur HTTP sur " + label + " : " + str(e))
        return resultats
    except requests.exceptions.RequestException as e:
        print("Erreur reseau sur " + label + " : " + str(e))
        return resultats

    # Analyser le HTML avec lxml
    tree = html.fromstring(reponse.content)
    tous_les_liens = tree.xpath("//a/@href")

    urls_visitees = set()
    compteur = 0

    for href in tous_les_liens:

        if compteur >= nb_articles:
            break

        if not href:
            continue

        if href.startswith("/"):
            href = "https://www.francetvinfo.fr" + href

        if "francetvinfo.fr" not in href:
            continue

        chemins_interdits = [
            ".jpg", ".png", ".mp4", ".gif",
            "/recherche/", "/profile/",
            "/mail/", "/user/", "/auth/",
            "/live/", "/en-direct/",
            "?", "#",
            "/tags/", "/auteur/",
            "/videos/", "/emissions/",
        ]
        if any(chemin in href for chemin in chemins_interdits):
            continue

        if not href.endswith(".html"):
            continue

        if href in urls_visitees:
            continue
        urls_visitees.add(href)

        try:
            reponse_article = requests.get(href, headers=HEADERS, timeout=10)
            reponse_article.raise_for_status()
        except requests.exceptions.Timeout:
            print("Timeout sur : " + href)
            continue
        except requests.exceptions.HTTPError:
            print("Erreur HTTP sur : " + href)
            continue
        except requests.exceptions.RequestException:
            print("Erreur reseau sur : " + href)
            continue

        # Extraire le texte avec lxml
        tree_article = html.fromstring(reponse_article.content)
        paragraphes = tree_article.xpath("//p//text()")

        if paragraphes:
            texte_brut = "\n".join(paragraphes)
        else:
            texte_brut = " ".join(tree_article.xpath("//text()"))

        lignes_propres = []
        for ligne in texte_brut.splitlines():
            ligne_nettoyee = ligne.strip()
            if ligne_nettoyee:
                lignes_propres.append(ligne_nettoyee)

        texte_final = "\n".join(lignes_propres)

        if len(texte_final) < 300:
            print("Article trop court ignore : " + href)
            continue

        resultats.append({
            "url":   href,
            "texte": texte_final,
            "label": label
        })

        print("Article " + str(compteur + 1) + "/" + str(nb_articles) + " [" + label + "] : " + href)
        compteur += 1
        time.sleep(1)

    return resultats


def sauvegarder_csv(donnees, nom_fichier):
    """
    Sauvegarde les articles dans un fichier CSV.
    Entree : donnees (list), nom_fichier (str)
    Sortie : fichier CSV sur le disque
    """
    fichier_existe = os.path.exists(nom_fichier)

    with open(nom_fichier, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "texte", "label"])
        if not fichier_existe:
            writer.writeheader()
        for article in donnees:
            writer.writerow(article)

    print(str(len(donnees)) + " articles sauvegardes dans " + nom_fichier)


def afficher_statistiques(nom_fichier):
    """
    Affiche les statistiques du dataset.
    Entree : nom_fichier (str)
    Sortie : affichage dans le terminal
    """
    if not os.path.exists(nom_fichier):
        print("Fichier CSV introuvable.")
        return

    stats = {}
    longueurs = []

    with open(nom_fichier, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for ligne in reader:
            label = ligne["label"]
            texte = ligne["texte"]
            if label not in stats:
                stats[label] = 0
            stats[label] += 1
            longueurs.append(len(texte))

    total = sum(stats.values())
    longueur_moyenne = sum(longueurs) / len(longueurs) if longueurs else 0

    print("\n--- STATISTIQUES DU DATASET ---")
    print("Total articles   : " + str(total))
    print("Longueur moyenne : " + str(int(longueur_moyenne)) + " caracteres")
    print("\nRepartition par label :")
    for label, count in stats.items():
        print("  " + label + " : " + str(count) + " articles")
    print("-------------------------------\n")


if __name__ == "__main__":

    print("Debut du scraping...")

    if os.path.exists(FICHIER_CSV):
        os.remove(FICHIER_CSV)
        print("Ancien fichier supprime.")

    for label, url in SECTIONS.items():
        print("\nSection : " + label)
        articles = scraper_section(url, label, NB_ARTICLES)
        if articles:
            sauvegarder_csv(articles, FICHIER_CSV)
        else:
            print("Aucun article recupere pour : " + label)

    afficher_statistiques(FICHIER_CSV)
    print("Scraping termine. Fichier cree : " + FICHIER_CSV)
