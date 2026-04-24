# -*- coding: utf-8 -*-
import requests
from lxml import html
import csv
import time
import os
import re

SECTIONS = {
    "politique": "https://www.francetvinfo.fr/politique/",
    "sport":     "https://www.francetvinfo.fr/sports/",
    "economie":  "https://www.francetvinfo.fr/economie/",
    "sante":     "https://www.francetvinfo.fr/sante/",
    "sciences":  "https://www.francetvinfo.fr/sciences/",
}

NB_ARTICLES = 10
FICHIER_CSV = "articles.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

MOTS_PARASITES = [
    "Recevez l", "Inscription", "newsletter", "Pour sauvegarder",
    "Sans paiement", "Suivez-nous", "Retrouvez aussi", "Flash info",
    "Confirmer votre", "France T", "toute l'actu", "Vous pouvez changer",
    "Activez les notifications", "Merci !", "Votre inscription",
    "exercer vos droits", "politique de confidentialit",
    "Pas encore de compte", "A regarder", "regarder",
]


def nettoyer_texte(texte):
    """
    Nettoie le texte : supprime les \n, \t et espaces multiples.
    Entree : texte (str)
    Sortie : texte propre (str)
    """
    texte = texte.replace("\\n", " ")
    texte = texte.replace("\n", " ")
    texte = texte.replace("\t", " ")
    texte = re.sub(r" {2,}", " ", texte)
    return texte.strip()


def extraire_label_depuis_url(url):
    """
    Extrait le label depuis l'URL.
    Entree : url (str)
    Sortie : label (str) ou None
    Complexite : O(k)
    """
    parties = url.replace("https://www.francetvinfo.fr/", "").split("/")
    for label in SECTIONS.keys():
        if label in parties or (label == "sport" and "sports" in parties):
            return label
    return None


def extraire_metadonnees(tree, url):
    """
    Extrait les metadonnees d'un article.
    Entree : tree (lxml.html), url (str)
    Sortie : dict {titre, date, chapeau, label}
    Complexite : O(n)
    """
    titre = ""
    h1 = tree.xpath("//h1//text()")
    if h1:
        titre = nettoyer_texte(" ".join(h1))
    else:
        title_tag = tree.xpath("//title//text()")
        if title_tag:
            titre = nettoyer_texte(title_tag[0])

    date = ""
    time_tag = tree.xpath("//time/@datetime")
    if time_tag:
        date = time_tag[0].strip()
    else:
        meta_date = tree.xpath("//meta[@property='article:published_time']/@content")
        if meta_date:
            date = meta_date[0].strip()

    chapeau = ""
    meta_desc = tree.xpath("//meta[@name='description']/@content")
    if meta_desc:
        chapeau = nettoyer_texte(meta_desc[0])

    label = extraire_label_depuis_url(url)
    return {"titre": titre, "date": date, "chapeau": chapeau, "label": label}


def est_parasite(ligne):
    """
    Detecte si une ligne est du contenu parasite.
    Entree : ligne (str)
    Sortie : bool
    """
    for mot in MOTS_PARASITES:
        if mot.lower() in ligne.lower():
            return True
    return False


def extraire_texte_article(tree):
    """
    Extrait le texte propre du corps de l'article.
    Cible la balise <article> pour eviter menus/newsletters.
    Entree : tree (lxml.html)
    Sortie : texte (str) nettoye, sans parasites, sans \\n
    Complexite : O(n)
    """
    # Strategie 1 : balise <article>
    paragraphes = tree.xpath("//article//p//text()")

    # Strategie 2 : classes CSS
    if not paragraphes:
        paragraphes = tree.xpath(
            "//*[contains(@class,'article') or contains(@class,'content')"
            " or contains(@class,'body') or contains(@class,'main')]//p//text()"
        )

    # Strategie 3 : fallback
    if not paragraphes:
        paragraphes = tree.xpath("//p//text()")

    lignes_propres = []
    for ligne in paragraphes:
        ligne = nettoyer_texte(ligne)
        if len(ligne) < 25:
            continue
        if est_parasite(ligne):
            continue
        lignes_propres.append(ligne)

    return " ".join(lignes_propres)


def scraper_section(url_section, label, nb_articles=10):
    """
    Recupere les articles d'une section France Info.
    Entree : url_section (str), label (str), nb_articles (int)
    Sortie : liste de dicts {url, titre, date, chapeau, texte, label}
    Complexite : O(nb_articles * T_reseau)
    """
    resultats = []

    try:
        reponse = requests.get(url_section, headers=HEADERS, timeout=10)
        reponse.raise_for_status()
    except requests.exceptions.Timeout:
        print("Timeout section : " + label)
        return resultats
    except requests.exceptions.HTTPError as e:
        print("Erreur HTTP " + label + " : " + str(e))
        return resultats
    except requests.exceptions.RequestException as e:
        print("Erreur reseau " + label + " : " + str(e))
        return resultats

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

        section_url = label if label != "sport" else "sports"
        if "/" + section_url + "/" not in href:
            continue

        chemins_interdits = [
            ".jpg", ".png", ".mp4", ".gif",
            "/recherche/", "/live/", "/en-direct/",
            "?", "#", "/tags/", "/auteur/", "/videos/",
        ]
        if any(c in href for c in chemins_interdits):
            continue
        if not href.endswith(".html"):
            continue
        if href in urls_visitees:
            continue
        urls_visitees.add(href)

        try:
            r = requests.get(href, headers=HEADERS, timeout=10)
            r.raise_for_status()
        except requests.exceptions.Timeout:
            print("Timeout : " + href)
            continue
        except requests.exceptions.HTTPError:
            print("Erreur HTTP : " + href)
            continue
        except requests.exceptions.RequestException:
            print("Erreur reseau : " + href)
            continue

        tree_article = html.fromstring(r.content)
        meta = extraire_metadonnees(tree_article, href)
        texte_final = extraire_texte_article(tree_article)

        if len(texte_final) < 200:
            print("Trop court, ignore : " + href)
            continue

        resultats.append({
            "url":     href,
            "titre":   meta["titre"],
            "date":    meta["date"],
            "chapeau": meta["chapeau"],
            "texte":   texte_final,
            "label":   label
        })

        print("OK " + str(compteur+1) + "/" + str(nb_articles)
              + " [" + label + "] " + meta["titre"][:60])
        compteur += 1
        time.sleep(1)

    return resultats


def sauvegarder_csv(donnees, nom_fichier):
    """
    Sauvegarde les articles en CSV UTF-8.
    Entree : donnees (list[dict]), nom_fichier (str)
    Sortie : fichier CSV
    Complexite : O(n)
    """
    fichier_existe = os.path.exists(nom_fichier)
    with open(nom_fichier, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["url", "titre", "date", "chapeau", "texte", "label"]
        )
        if not fichier_existe:
            writer.writeheader()
        for article in donnees:
            writer.writerow(article)
    print(str(len(donnees)) + " articles sauvegardes.")


def afficher_statistiques(nom_fichier):
    """
    Affiche les stats du dataset.
    Entree : nom_fichier (str)
    Complexite : O(n)
    """
    if not os.path.exists(nom_fichier):
        print("Fichier introuvable.")
        return

    stats = {}
    longueurs = []

    with open(nom_fichier, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for ligne in reader:
            stats[ligne["label"]] = stats.get(ligne["label"], 0) + 1
            longueurs.append(len(ligne["texte"]))

    print("\n--- STATISTIQUES ---")
    print("Total : " + str(sum(stats.values())) + " articles")
    print("Longueur moyenne : " + str(int(sum(longueurs)/len(longueurs))) + " car.")
    for label, count in stats.items():
        print("  " + label + " : " + str(count))
    print("--------------------\n")


if __name__ == "__main__":
    print("Debut du scraping...")

    if os.path.exists(FICHIER_CSV):
        os.remove(FICHIER_CSV)

    for label, url in SECTIONS.items():
        print("\n=== Section : " + label + " ===")
        articles = scraper_section(url, label, NB_ARTICLES)
        if articles:
            sauvegarder_csv(articles, FICHIER_CSV)
        else:
            print("Aucun article pour : " + label)

    afficher_statistiques(FICHIER_CSV)
    print("Termine ! Fichier : " + FICHIER_CSV)
