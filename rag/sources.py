"""Mapping source du corpus → URL publique de la fiche sur le site statique.

Le site (https://permis-bateau.legrand.sh) publie la racine du repo telle
quelle — `netlify.toml` a `publish = "."` — donc le chemin d'un document du
corpus EST son chemin sur le site : `lessons/0004-balisage-maritime.html` →
`https://permis-bateau.legrand.sh/lessons/0004-balisage-maritime.html`.

Une exception : les `learning-records/*.md` ne sont pas des pages publiées
(vérifié : 404 sur le site). Ce sont les notes de travail internes, elles
n'ont pas d'URL et restent affichées sans lien.
"""
import os

# Surchargeable pour un déploiement sur un autre domaine ou un preview Netlify.
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://permis-bateau.legrand.sh").rstrip("/")

# Préfixes de sources réellement publiés comme pages du site.
PUBLISHED_PREFIXES = ("lessons/", "reference/")


def source_url(source: str) -> str | None:
    """URL publique de la fiche, ou None si la source n'est pas publiée."""
    if not source.startswith(PUBLISHED_PREFIXES):
        return None
    return f"{SITE_BASE_URL}/{source}"


def source_label(source: str) -> str:
    """Nom lisible d'une source : « 0004-balisage-maritime ».

    Les learning-records sont préfixés « note · » : ils portent le même nom de
    fichier que la leçon dont ils sont les notes
    (`learning-records/0006-securite-equipements.md` vs
    `lessons/0006-securite-equipements.html`), donc sans préfixe la marge
    affichait deux lignes identiques dont une seule cliquable.
    """
    name = source.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    if source.startswith("learning-records/"):
        return f"note · {name}"
    return name
