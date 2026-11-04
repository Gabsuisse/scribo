#!/usr/bin/env python3
"""
lint_scribo.py : couche deterministe du controle qualite d'un lot Scribo.

Ce script ne modifie rien. Il lit le depot, applique les regles qui se verifient
par calcul ou par recherche, puis rend un rapport. L'agent Lint s'en sert comme
reference, puis relit ce qu'un script ne voit pas (voir agent-lint.md).

Usage (depuis la racine du depot) :
    python3 lint/lint_scribo.py                 controle de l'etat du depot
    python3 lint/lint_scribo.py --lot 05        controle du lot 05 (brief, passation, registre)
    python3 lint/lint_scribo.py --md            sortie en lignes de tableau pour le rapport
    python3 lint/lint_scribo.py --json          sortie lisible par une machine
    python3 lint/lint_scribo.py --root CHEMIN   depot a controler (par defaut : le depot du script)

Sans dependance (bibliotheque standard), Python 3.10 ou plus.
Si besoin :  uv run --no-project lint/lint_scribo.py

Code de sortie : 0 aucun constat bloquant, 1 au moins un constat bloquant, 2 erreur d'usage.
"""
from __future__ import annotations

import argparse
import ast
import datetime
import html
import importlib.util
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("lint_scribo.py demande Python 3.10 ou plus. Essaie : uv run --no-project lint/lint_scribo.py")

sys.dont_write_bytecode = True

VERSION_SCRIPT = "1.0.0"
BLOQUANT, AVERT, RELIRE = "BLOQUANT", "AVERTISSEMENT", "A_RELIRE"

PAGES_LANDING = {"scribo.html", "index.html"}
EXCLU_COMMUN = {".git", ".venv", "node_modules", "__pycache__", "pdfjs"}
EXCLU_CODE = EXCLU_COMMUN | {"docs", "lint", "lots", "gabarits", "_brouillon"}


@dataclass
class Constat:
    regle: str
    gravite: str
    fichier: str
    ligne: int
    message: str
    invariant: str
    correction: str


CONSTATS: list[Constat] = []
REUSSIES: dict[str, str] = {}
NON_VERIFIABLES: list[tuple[str, str]] = []


def ajouter(regle, gravite, fichier, ligne, message, invariant, correction):
    CONSTATS.append(Constat(regle, gravite, fichier, ligne, message, invariant, correction))


def reussie(regle, detail):
    REUSSIES[regle] = (REUSSIES[regle] + " ; " + detail) if regle in REUSSIES else detail


# ---------------------------------------------------------------- utilitaires

def lire(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def ligne_de(texte: str, pos: int) -> int:
    return texte.count("\n", 0, pos) + 1


def fichiers(root: Path, suffixes: set[str], exclus: set[str]):
    for dossier, sous, noms in os.walk(root):
        sous[:] = sorted(d for d in sous if d not in exclus)
        for nom in sorted(noms):
            p = Path(dossier) / nom
            if p.suffix.lower() in suffixes:
                yield p


def rel(root: Path, p: Path) -> str:
    return str(p.relative_to(root))


def arbre(p: Path):
    try:
        return ast.parse(lire(p))
    except SyntaxError:
        return None


# ------------------------------------------------------------------------ R01

MOTIFS_RESEAU = [
    (r'<link\b[^>]*\bhref\s*=\s*["\'](?:https?:)?//', "ressource <link> distante"),
    (r'<script\b[^>]*\bsrc\s*=\s*["\'](?:https?:)?//', "script distant"),
    (r'<(?:img|source|iframe|video|audio|embed|object)\b[^>]*\b(?:src|data)\s*=\s*["\'](?:https?:)?//', "media ou cadre distant"),
    (r'@import\s+(?:url\()?\s*["\']?(?:https?:)?//', "@import CSS distant"),
    (r'url\(\s*["\']?(?:https?:)?//', "url() CSS distante"),
    (r'\bfetch\(\s*["\'`](?:https?:)?//', "fetch vers une URL distante"),
    (r'new\s+WebSocket\(\s*["\'`]wss?://', "WebSocket distant"),
    (r'\.open\(\s*["\']\w+["\']\s*,\s*["\'`](?:https?:)?//', "XMLHttpRequest vers une URL distante"),
    (r'sendBeacon\(\s*["\'`](?:https?:)?//', "sendBeacon distant"),
    (r'\bimport\(\s*["\'`](?:https?:)?//', "import dynamique distant"),
    (r'importScripts\(\s*["\'`](?:https?:)?//', "importScripts distant"),
]
HOTES_LOCAUX = {"localhost", "127.0.0.1", "0.0.0.0", "[::1]"}
MODULES_RESEAU = {"urllib.request", "urllib3", "requests", "httpx", "aiohttp", "http.client",
                  "ftplib", "smtplib", "telnetlib", "websockets", "websocket", "huggingface_hub"}


def hote_local(url: str) -> bool:
    m = re.match(r'(?:https?:)?//([^/:\s"\'`]+)', url)
    return bool(m) and m.group(1).lower() in HOTES_LOCAUX


def regle_r01(root: Path):
    inv = "Zero reseau"
    nb = 0
    for p in fichiers(root, {".html", ".htm", ".js", ".css"}, EXCLU_CODE):
        if p.name in PAGES_LANDING:
            continue
        nb += 1
        texte = lire(p)
        for motif, libelle in MOTIFS_RESEAU:
            for m in re.finditer(motif, texte, re.I):
                extrait = texte[m.start(): m.end() + 200]
                u = re.search(r'(?:https?:)?//[^\s"\'`)>]+', extrait)
                if u and hote_local(u.group(0)):
                    continue
                cible = u.group(0) if u else extrait[:60]
                ajouter("R01", BLOQUANT, rel(root, p), ligne_de(texte, m.start()),
                        f"{libelle} : {cible}", inv,
                        "Embarquer la ressource en local dans le depot (fichier servi par le serveur local).")
    for p in fichiers(root, {".py"}, EXCLU_CODE):
        nb += 1
        t = arbre(p)
        if t is None:
            continue
        for noeud in ast.walk(t):
            noms = []
            if isinstance(noeud, ast.Import):
                noms = [a.name for a in noeud.names]
            elif isinstance(noeud, ast.ImportFrom) and noeud.level == 0 and noeud.module:
                noms = [noeud.module]
            for nom in noms:
                if any(nom == mod or nom.startswith(mod + ".") for mod in MODULES_RESEAU):
                    ajouter("R01", BLOQUANT, rel(root, p), noeud.lineno,
                            f"import d'un module capable d'appeler le reseau : {nom}", inv,
                            "Retirer l'import, ou le justifier par une decision dans decisions.md.")
    if not any(c.regle == "R01" for c in CONSTATS):
        reussie("R01", f"{nb} fichiers de l'app sans appel reseau (landing exclue)")


# ------------------------------------------------------------------------ R03

def charger_extracteur(root: Path):
    chemin = root / "extracteur.py"
    if not chemin.exists():
        return None, "extracteur.py introuvable"
    try:
        spec = importlib.util.spec_from_file_location("scribo_extracteur", chemin)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, None
    except Exception as e:  # noqa: BLE001
        return None, f"import impossible : {e!r}"


def regle_r03(root: Path):
    inv = "Verification deterministe"
    mod, err = charger_extracteur(root)
    if mod is None:
        NON_VERIFIABLES.append(("R03", err))
        return
    auj = datetime.date.today()
    jour_suivant = auj + datetime.timedelta(days=1)

    def siecle_naissance():
        mauvais = []
        for aa in range(100):
            r = mod._mrz_date_vers_iso(f"{aa:02d}0101", True)
            if r is None or datetime.date.fromisoformat(r) > auj:
                mauvais.append((aa, r))
        return True if not mauvais else f"date de naissance nulle ou future pour aa={mauvais[:4]}"

    def siecle_suivant():
        aa = (auj.year + 1) % 100
        r = mod._mrz_date_vers_iso(f"{aa:02d}0101", True)
        attendu = f"{auj.year + 1 - 100:04d}-01-01"
        return True if r == attendu else f"attendu {attendu}, obtenu {r}"

    def siecle_courant():
        aa = auj.year % 100
        r = mod._mrz_date_vers_iso(f"{aa:02d}0101", True)
        attendu = f"{auj.year:04d}-01-01"
        return True if r == attendu else f"attendu {attendu}, obtenu {r}"

    def expiration():
        mauvais = []
        for aa in range(100):
            r = mod._mrz_date_vers_iso(f"{aa:02d}0101", False)
            if r is None or int(r[:4]) < auj.year - 10:
                mauvais.append((aa, r))
        return True if not mauvais else f"expiration hors fenetre pour aa={mauvais[:4]}"

    tests = [
        ("mrz_cle numero ICAO L898902C3 donne 6", lambda: mod.mrz_cle("L898902C3") == 6),
        ("mrz_cle naissance ICAO 740812 donne 2", lambda: mod.mrz_cle("740812") == 2),
        ("mrz_cle expiration ICAO 120415 donne 9", lambda: mod.mrz_cle("120415") == 9),
        ("mrz_cle zone facultative ICAO donne 1", lambda: mod.mrz_cle("ZE184226B<<<<<<") == 1),
        ("mrz_champ_valide : cle juste, cle fausse, champ vide",
         lambda: (mod.mrz_champ_valide("L898902C3", "6"), mod.mrz_champ_valide("L898902C3", "5"),
                  mod.mrz_champ_valide("", "6")) == (True, False, None)),
        ("iban_valide : exemples valides GB, FR, DE",
         lambda: all(mod.iban_valide(i) for i in ("GB82WEST12345698765432",
                                                  "FR1420041010050500013M02606",
                                                  "DE89370400440532013000"))),
        ("iban_valide : un chiffre modifie est refuse",
         lambda: not any(mod.iban_valide(i) for i in ("GB82WEST12345698765433",
                                                      "FR1420041010050500013M02607"))),
        ("bic_valide : PSSTFRPPXXX accepte, 123 refuse",
         lambda: mod.bic_valide("PSSTFRPPXXX") is True and mod.bic_valide("123") is False),
        ("_mrz_parse_noms : exemple ICAO ERIKSSON / ANNA MARIA",
         lambda: mod._mrz_parse_noms("P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<") == ("ERIKSSON", "ANNA MARIA")),
        ("regle du siecle : naissance jamais dans le futur (aa de 00 a 99)", siecle_naissance),
        ("regle du siecle : annee suivante renvoie le siecle precedent", siecle_suivant),
        ("regle du siecle : annee courante reste dans le siecle courant", siecle_courant),
        ("regle du siecle : expiration dans une fenetre proche du present", expiration),
    ]
    echecs = []
    for nom, f in tests:
        try:
            res = f()
        except Exception as e:  # noqa: BLE001
            res = f"exception {e!r}"
        if res is not True:
            echecs.append(nom)
            detail = "" if res is False else f" ({res})"
            ajouter("R03", BLOQUANT, "extracteur.py", 0, f"Test en echec : {nom}{detail}", inv,
                    "Corriger la fonction de verification concernee, sans modifier le test.")
    if not echecs:
        reussie("R03", f"{len(tests)} tests de verification passent")

    # limite connue : la regle du siecle ne compare que les annees
    if jour_suivant.year == auj.year:
        aa = auj.year % 100
        r = mod._mrz_date_vers_iso(f"{aa:02d}{jour_suivant.month:02d}{jour_suivant.day:02d}", True)
        if r and datetime.date.fromisoformat(r) > auj:
            ajouter("R03", AVERT, "extracteur.py", 0,
                    f"Limite connue : une date de naissance MRZ situee plus tard dans l'annee courante est acceptee "
                    f"({r}, apres aujourd'hui). La regle du siecle ne compare que les annees.", inv,
                    "Decision a prendre : comparer la date complete. Hors lot si ce n'est pas tranche.")


# ------------------------------------------------------------------------ R04

ALIAS_IMPORT = {"fitz": "pymupdf", "mlx_lm": "mlx-lm", "cv2": "opencv-python", "PIL": "pillow",
                "yaml": "pyyaml", "bs4": "beautifulsoup4", "sklearn": "scikit-learn"}
IMPLIQUES = {"mlx": {"mlx", "mlx-lm"}}


def normaliser_dist(nom: str) -> str:
    return re.sub(r"[-_.]+", "-", nom.strip().lower())


def dependances_declarees(root: Path):
    f = root / "pyproject.toml"
    if not f.exists():
        return None
    t = lire(f)
    m = re.search(r"^dependencies\s*=\s*\[(.*?)\]", t, re.M | re.S)
    if not m:
        return set()
    return {normaliser_dist(x) for x in re.findall(r'"\s*([A-Za-z0-9_.\-]+)', m.group(1))}


def regle_r04(root: Path):
    declarees = dependances_declarees(root)
    if declarees is None:
        NON_VERIFIABLES.append(("R04", "pyproject.toml introuvable"))
        return
    stdlib = set(sys.stdlib_module_names)
    locaux = {p.stem for p in root.glob("*.py")} | {d.name for d in root.iterdir() if d.is_dir()}
    vus = {}
    for p in fichiers(root, {".py"}, EXCLU_CODE):
        t = arbre(p)
        if t is None:
            continue
        for n in ast.walk(t):
            noms = []
            if isinstance(n, ast.Import):
                noms = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                noms = [n.module]
            for nom in noms:
                racine = nom.split(".")[0]
                if racine in stdlib or racine in locaux or racine == "__future__":
                    continue
                vus.setdefault(racine, (rel(root, p), n.lineno))
    manquantes = 0
    for racine, (fichier, ligne) in sorted(vus.items()):
        dist = normaliser_dist(ALIAS_IMPORT.get(racine, racine))
        acceptes = IMPLIQUES.get(racine, {dist})
        if not (acceptes & declarees):
            manquantes += 1
            ajouter("R04", BLOQUANT, fichier, ligne,
                    f"Import de '{racine}' (paquet '{dist}') absent de pyproject.toml", "Dependances declarees",
                    "Declarer la dependance dans pyproject.toml si le brief la prevoit, sinon retirer l'import.")
    if not manquantes:
        reussie("R04", f"{len(vus)} dependances importees, toutes declarees ({', '.join(sorted(vus))})")


# ------------------------------------------------------------------------ R05

FICHIERS_BUILD = ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb",
                  "tailwind.config.js", "tailwind.config.ts", "tailwind.config.cjs", "tailwind.config.mjs",
                  "postcss.config.js", "postcss.config.cjs", "vite.config.js", "vite.config.ts",
                  "webpack.config.js", "rollup.config.js", "esbuild.config.js"]


def regle_r05(root: Path):
    inv = "Pas de chaine de build ni de Tailwind"
    trouve = False
    for nom in FICHIERS_BUILD:
        if (root / nom).exists():
            trouve = True
            ajouter("R05", BLOQUANT, nom, 0, f"Fichier de chaine de build present : {nom}", inv,
                    "Retirer le fichier ou ouvrir un workshop : la regle vaut pour tout le produit.")
    if (root / "node_modules").exists():
        trouve = True
        ajouter("R05", BLOQUANT, "node_modules", 0, "Dossier node_modules present", inv,
                "Retirer le dossier.")
    for p in fichiers(root, {".html", ".htm", ".js", ".css", ".py"}, EXCLU_CODE):
        t = lire(p)
        for m in re.finditer(r"tailwind", t, re.I):
            trouve = True
            ajouter("R05", BLOQUANT, rel(root, p), ligne_de(t, m.start()),
                    "Reference a Tailwind dans le code", inv, "Ecrire le style en CSS natif.")
            break
    if not trouve:
        reussie("R05", "aucune chaine de build, aucune reference a Tailwind")


# ------------------------------------------------------------------------ R06

RE_IBAN = re.compile(r"(?<![A-Za-z0-9])[A-Z]{2}\d{2}(?:[  ]?[A-Z0-9]{4}){2,7}(?:[  ]?[A-Z0-9]{1,4})?(?![A-Za-z0-9])")
RE_MRZ2 = re.compile(r"(?<![A-Z0-9<])[A-Z0-9<]{9}\d[A-Z<]{3}\d{6}\d[MF<]\d{6}\d[A-Z0-9<]{16}(?![A-Z0-9<])")
RE_MRZ1 = re.compile(r"(?<![A-Z0-9<])P[A-Z<][A-Z]{3}[A-Z<]{39}(?![A-Z0-9<])")


def iban_mod97(v: str) -> bool:
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", v):
        return False
    perm = v[4:] + v[:4]
    return int("".join(str(ord(c) - 55) if c.isalpha() else c for c in perm)) % 97 == 1


def norm_iban(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def regle_r06(root: Path):
    inv = "Donnees de demo fictives"
    f = root / "lint" / "specimens.json"
    if not f.exists():
        NON_VERIFIABLES.append(("R06", "lint/specimens.json introuvable : liste des specimens fictifs absente"))
        return
    try:
        spec = json.loads(lire(f))
    except json.JSONDecodeError as e:
        NON_VERIFIABLES.append(("R06", f"lint/specimens.json illisible : {e}"))
        return
    ibans_ok = {norm_iban(x) for x in spec.get("ibans", [])}
    mrz_ok = {re.sub(r"\s", "", x) for x in spec.get("mrz", [])}
    nb = 0
    anormaux = 0
    # lint/ est exclu : le script contient ses propres vecteurs de test (IBAN et MRZ publics de la norme)
    for p in fichiers(root, {".html", ".htm", ".js", ".py", ".md", ".json"}, EXCLU_COMMUN | {"lint", "_brouillon"}):
        t = html.unescape(lire(p))
        nb += 1
        for m in RE_IBAN.finditer(t):
            v = norm_iban(m.group(0))
            if not (15 <= len(v) <= 34):
                continue
            valide = iban_mod97(v)
            forme_fr = v.startswith("FR") and len(v) == 27
            if not (valide or forme_fr) or v in ibans_ok:
                continue
            anormaux += 1
            if valide:
                ajouter("R06", BLOQUANT, rel(root, p), ligne_de(t, m.start()),
                        f"IBAN valide hors liste des specimens : {m.group(0).strip()}", inv,
                        "S'il est fictif, l'ajouter a lint/specimens.json avec une decision. S'il est reel, le retirer.")
            else:
                ajouter("R06", AVERT, rel(root, p), ligne_de(t, m.start()),
                        f"Chaine de forme IBAN francais sans cle valide, hors liste : {m.group(0).strip()}", inv,
                        "Probablement un exemple de documentation. Le confirmer ou le retirer.")
        for motif in (RE_MRZ2, RE_MRZ1):
            for m in motif.finditer(t):
                if m.group(0) in mrz_ok:
                    continue
                anormaux += 1
                ajouter("R06", BLOQUANT, rel(root, p), ligne_de(t, m.start()),
                        f"Ligne MRZ hors liste des specimens : {m.group(0)[:20]}...", inv,
                        "Si elle est fictive, l'ajouter a lint/specimens.json avec une decision. Sinon la retirer.")
    if not anormaux:
        reussie("R06", f"{nb} fichiers scannes, tous les IBAN et MRZ trouves sont des specimens listes")


# ------------------------------------------------------------------------ R07

def regle_r07(root: Path):
    inv = "Fichiers temporaires supprimes"
    nb = 0
    anomalie = False
    for p in fichiers(root, {".py"}, EXCLU_CODE):
        t = arbre(p)
        if t is None:
            continue
        for fonction in [n for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            creations = []
            for n in ast.walk(fonction):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in (
                        "NamedTemporaryFile", "mkstemp", "mkdtemp"):
                    sans_suppression_auto = n.func.attr != "NamedTemporaryFile" or any(
                        k.arg == "delete" and isinstance(k.value, ast.Constant) and k.value.value is False
                        for k in n.keywords)
                    if sans_suppression_auto:
                        creations.append(n)
            if not creations:
                continue
            suppressions_finally = 0
            for tr in [n for n in ast.walk(fonction) if isinstance(n, ast.Try)]:
                for s in tr.finalbody:
                    for c in ast.walk(s):
                        if isinstance(c, ast.Call):
                            nom = c.func.attr if isinstance(c.func, ast.Attribute) else getattr(c.func, "id", "")
                            if nom in ("unlink", "remove", "rmtree", "rmdir"):
                                suppressions_finally += 1
            nb += len(creations)
            if suppressions_finally == 0:
                anomalie = True
                ajouter("R07", BLOQUANT, rel(root, p), creations[0].lineno,
                        f"Fichier temporaire cree dans {fonction.name}() sans suppression dans un bloc finally", inv,
                        "Supprimer le fichier dans un finally pour couvrir aussi les erreurs.")
    if not anomalie:
        reussie("R07", f"{nb} fichier(s) temporaire(s), suppression dans un finally")


# ------------------------------------------------------------------------ R08

def meta(texte: str):
    tete = "\n".join(texte.splitlines()[:40])
    d = re.search(r"^Date\s*:\s*(\S+)", tete, re.M)
    lot = re.search(r"^Lot\s*:\s*n\D*(\d+)", tete, re.M)
    v = re.search(r"^Version produit\s*:\s*v?(\d+\.\d+\.\d+)", tete, re.M)
    return (d.group(1) if d else None, int(lot.group(1)) if lot else None, v.group(1) if v else None)


def premiere_ligne_historique(texte: str):
    i = texte.find("## Historique")
    if i < 0:
        return None
    m = re.search(r"^-\s*v(\d+\.\d+\.\d+)\s*\(([^)]*)\)", texte[i:], re.M)
    if not m:
        return None
    lot = re.search(r"Lot\s*(\d+)", m.group(2))
    return m.group(1), (int(lot.group(1)) if lot else None)


def regle_r08(root: Path, lot_arg: str | None):
    inv = "Versions et docs coherentes"
    infos = {}
    for nom in ("agent.md", "design.md"):
        p = root / nom
        if not p.exists():
            ajouter("R08", BLOQUANT, nom, 0, f"{nom} introuvable", inv, "Restaurer le fichier de reference.")
            continue
        t = lire(p)
        d, lot, v = meta(t)
        if None in (d, lot, v):
            ajouter("R08", BLOQUANT, nom, 1, "Bloc meta incomplet (Date, Lot, Version produit)", inv,
                    "Ajouter les trois lignes en tete du fichier.")
            continue
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", d):
            ajouter("R08", AVERT, nom, 1, f"Date au format inattendu : {d}", inv, "Utiliser JJ/MM/AAAA.")
        h = premiere_ligne_historique(t)
        if h is None:
            ajouter("R08", BLOQUANT, nom, 0, "Aucune ligne d'historique trouvee sous '## Historique'", inv,
                    "Ajouter une ligne : - vX.Y.Z (Lot N, JJ/MM/AAAA) : description.")
        else:
            if h[0] != v:
                ajouter("R08", BLOQUANT, nom, 0,
                        f"Version du bloc meta (v{v}) differente de la derniere ligne d'historique (v{h[0]})", inv,
                        "Aligner le bloc meta et l'historique.")
            if h[1] is not None and h[1] != lot:
                ajouter("R08", BLOQUANT, nom, 0,
                        f"Lot du bloc meta (n{lot}) different du lot de la derniere ligne d'historique (n{h[1]})", inv,
                        "Aligner le bloc meta et l'historique.")
        infos[nom] = (d, lot, v)
    if len(infos) == 2:
        a, g = infos["agent.md"], infos["design.md"]
        if a[2] != g[2]:
            ajouter("R08", BLOQUANT, "agent.md / design.md", 0, f"Versions differentes : v{a[2]} et v{g[2]}", inv,
                    "Les deux fichiers portent la meme version produit.")
        if a[1] != g[1]:
            ajouter("R08", BLOQUANT, "agent.md / design.md", 0, f"Lots differents : n{a[1]} et n{g[1]}", inv,
                    "Les deux fichiers portent le meme numero de lot.")
    version_doc = infos.get("agent.md", (None, None, None))[2]
    lot_doc = infos.get("agent.md", (None, None, None))[1]

    pp = root / "pyproject.toml"
    if pp.exists() and version_doc:
        m = re.search(r'^version\s*=\s*"([^"]+)"', lire(pp), re.M)
        if m and m.group(1) != version_doc:
            ajouter("R08", AVERT, "pyproject.toml", 0,
                    f"Version de pyproject.toml ({m.group(1)}) differente de la version produit (v{version_doc})", inv,
                    "Aligner pyproject.toml sur la version produit, a la fusion du lot.")

    for nom in ("decisions.md", "lots/REGISTRE.md"):
        if not (root / nom).exists():
            ajouter("R08", BLOQUANT, nom, 0, f"{nom} introuvable", inv, "Restaurer le fichier du dispositif.")

    if lot_arg:
        n = int(lot_arg)
        dossier = root / "lots" / f"lot-{n:02d}"
        brief = dossier / "brief.md"
        if not brief.exists():
            ajouter("R08", BLOQUANT, f"lots/lot-{n:02d}/brief.md", 0, "Dossier de lot introuvable", inv,
                    "Le brief du workshop doit etre dans le depot avant le code.")
        else:
            bt = lire(brief)
            ml = re.search(r"^Lot\s*:\s*n\D*(\d+)", bt, re.M)
            mv = re.search(r"^Version produit propos\S*\s*:\s*v?(\d+\.\d+\.\d+)", bt, re.M)
            if not ml or int(ml.group(1)) != n:
                ajouter("R08", BLOQUANT, rel(root, brief), 0, f"Le brief ne porte pas le lot n{n}", inv,
                        "Corriger le numero de lot du brief.")
            if mv and version_doc and mv.group(1) != version_doc:
                ajouter("R08", BLOQUANT, rel(root, brief), 0,
                        f"Version proposee par le brief (v{mv.group(1)}) differente de celle des docs (v{version_doc})", inv,
                        "Appliquer la version du brief dans agent.md, design.md et l'historique.")
            if not mv:
                ajouter("R08", BLOQUANT, rel(root, brief), 0, "Version produit proposee absente du brief", inv,
                        "Renseigner la version dans le brief.")
        if lot_doc is not None and lot_doc != n:
            ajouter("R08", BLOQUANT, "agent.md", 0, f"Le bloc meta indique le lot n{lot_doc}, le lot controle est n{n}", inv,
                    "Mettre a jour le bloc meta de agent.md et design.md.")
        if not (dossier / "passation.md").exists():
            ajouter("R08", BLOQUANT, f"lots/lot-{n:02d}/passation.md", 0, "Passation absente", inv,
                    "L'agent Code ecrit la passation avant de rendre la main.")
        reg = root / "lots" / "REGISTRE.md"
        if reg.exists() and not re.search(rf"^\|\s*0*{n}\s*\|", lire(reg), re.M):
            ajouter("R08", BLOQUANT, "lots/REGISTRE.md", 0, f"Le lot {n} n'a pas de ligne dans le registre", inv,
                    "Ajouter la ligne du lot au registre.")
    if not any(c.regle == "R08" for c in CONSTATS):
        reussie("R08", f"docs coherents (lot {lot_doc}, v{version_doc})" + (f", dossier du lot {lot_arg} complet" if lot_arg else ""))


# ------------------------------------------------------------------------ R09

def regle_r09(root: Path):
    inv = "Tokens de design"
    nb = 0
    for p in fichiers(root, {".html", ".htm", ".css"}, EXCLU_CODE):
        t = lire(p)
        nb += 1
        declarees = set(re.findall(r"(--[\w-]+)\s*:", t)) | set(re.findall(r"setProperty\(\s*['\"](--[\w-]+)", t))
        deja = set()
        for m in re.finditer(r"var\(\s*(--[\w-]+)\s*(,?)", t):
            nom, fallback = m.group(1), m.group(2)
            if fallback or nom in declarees or nom in deja:
                continue
            deja.add(nom)
            ajouter("R09", AVERT, rel(root, p), ligne_de(t, m.start()),
                    f"Variable CSS utilisee mais jamais declaree : var({nom})", inv,
                    f"Declarer {nom} dans :root, ou remplacer par un token existant.")
    if not any(c.regle == "R09" for c in CONSTATS):
        reussie("R09", f"{nb} fichiers, aucune variable CSS non declaree")


# ------------------------------------------------------------------------ R10

def regle_r10(root: Path):
    inv = "Etats d'interface documentes"
    app = root / "extractorultimator.html"
    design = root / "design.md"
    if not app.exists() or not design.exists():
        NON_VERIFIABLES.append(("R10", "extractorultimator.html ou design.md introuvable"))
        return
    lignes = lire(app).splitlines()
    debut = next((i for i, l in enumerate(lignes) if "const CATALOGUE" in l), None)
    if debut is None:
        NON_VERIFIABLES.append(("R10", "CATALOGUE introuvable dans extractorultimator.html"))
        return
    actives, courant = [], None
    for i in range(debut, min(debut + 120, len(lignes))):
        l = lignes[i]
        m = re.search(r'\{\s*id:"(\w+)"\s*,\s*nom:"([^"]+)"', l)
        if m:
            courant = (m.group(1), m.group(2), i + 1)
        if courant and "actif:true" in l.replace(" ", ""):
            actives.append(courant)
            courant = None
    dt = lire(design).lower()
    for ident, nom, ligne in actives:
        if nom.lower() not in dt:
            ajouter("R10", AVERT, "extractorultimator.html", ligne,
                    f"Famille active '{nom}' absente de design.md (artboards du canvas userflow)", inv,
                    "Ajouter les artboards de la famille au canvas userflow et le noter dans design.md section 2 bis.")
    liste = ", ".join(i for i, _, _ in actives)
    if not any(c.regle == "R10" for c in CONSTATS):
        reussie("R10", f"familles actives ({liste}) citees dans design.md")
    ajouter("R10", RELIRE, "extractorultimator.html", debut + 1,
            f"Familles actives : {liste}. Verifier que chacune a ses etats (statut, depot, scan, resultats, erreurs) dans design.md section 2 bis.",
            inv, "Relecture par l'agent Lint.")


# ------------------------------------------------------------------------ R11

def regle_r11(root: Path):
    inv = "Niveaux qualitatifs, pas de pourcentage"
    anomalie = False
    for p in fichiers(root, {".html", ".htm", ".js"}, EXCLU_CODE):
        brut = lire(p)
        t = re.sub(r"<style\b.*?</style>", lambda m: "\n" * m.group(0).count("\n"), brut, flags=re.S | re.I)
        t = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), t, flags=re.S)
        est_landing = p.name in PAGES_LANDING
        motifs = [r">\s*\d{1,3}\s?%\s*<"] if not est_landing else []
        motifs.append(r"(?:score|confiance|confidence|fiabilit\w*|reliab\w*)[^\n]{0,50}\d{1,3}\s?%")
        motifs.append(r"(?:score|confiance|confidence)[^\n]{0,50}\}\s?%")
        motifs.append(r"\d{1,3}\s?%[^\n]{0,30}(?:de confiance|confidence|de fiabilit\w*)")
        for motif in motifs:
            for m in re.finditer(motif, t, re.I):
                anomalie = True
                ajouter("R11", AVERT, rel(root, p), ligne_de(t, m.start()),
                        f"Pourcentage de confiance affiche : {m.group(0).strip()[:70]}", inv,
                        "Afficher Verifie, Probable ou A verifier a la place du pourcentage.")
    if not anomalie:
        reussie("R11", "aucun pourcentage de confiance dans l'interface")


# ------------------------------------------------------------------------ R13 + R02 (reperage)

SENSIBLES = {"texte", "brut", "champs", "valeur", "valeurs", "iban", "bic", "mrz", "donnees",
             "contenu", "resultat", "l1", "l2"}
NOMS_FICHIER = {"nom", "chemin", "filename"}


def noms_exposes(noeud) -> set[str]:
    if isinstance(noeud, ast.Call) and isinstance(noeud.func, ast.Name) and noeud.func.id == "len":
        return set()
    s = set()
    if isinstance(noeud, ast.Name):
        s.add(noeud.id)
    for enfant in ast.iter_child_nodes(noeud):
        s |= noms_exposes(enfant)
    return s


def regle_r13_r02(root: Path):
    inv13 = "Documents jamais journalises"
    n_appels = 0
    anomalie = False
    for p in fichiers(root, {".py"}, EXCLU_CODE):
        t = arbre(p)
        if t is None:
            continue
        exceptions = {n.name for n in ast.walk(t) if isinstance(n, ast.ExceptHandler) and n.name}
        for n in ast.walk(t):
            if not (isinstance(n, ast.Call) and (
                    (isinstance(n.func, ast.Name) and n.func.id == "print")
                    or (isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
                        and n.func.value.id in ("logging", "logger", "log")))):
                continue
            n_appels += 1
            noms = set()
            for a in list(n.args) + [k.value for k in n.keywords]:
                noms |= noms_exposes(a)
            contenu = noms & SENSIBLES
            if contenu:
                anomalie = True
                ajouter("R13", BLOQUANT, rel(root, p), n.lineno,
                        f"Affichage ou journal pouvant contenir le contenu d'un document : {', '.join(sorted(contenu))}",
                        inv13, "Ne journaliser ni le texte, ni les valeurs extraites. Une longueur ou un type suffisent.")
            if noms & NOMS_FICHIER:
                anomalie = True
                ajouter("R13", RELIRE, rel(root, p), n.lineno,
                        "Le nom du fichier depose est affiche dans la console : il peut contenir un nom de personne.",
                        inv13, "A confirmer par la relecture : acceptable en local, a decider.")
            if noms & exceptions:
                anomalie = True
                ajouter("R13", RELIRE, rel(root, p), n.lineno,
                        "Un message d'exception est affiche : il peut citer un extrait du document.",
                        inv13, "A confirmer par la relecture selon l'origine de l'exception.")
    if not anomalie:
        reussie("R13", f"{n_appels} affichage(s) console, aucun contenu de document")
    # reperage pour la relecture de R02
    ex = root / "extracteur.py"
    if ex.exists():
        t = lire(ex)
        for m in re.finditer(r'return\s+"verifie"|"Vérifié\s*·', t):
            ajouter("R02", RELIRE, "extracteur.py", ligne_de(t, m.start()),
                    "Point d'attribution du niveau Verifie : verifier que la valeur controlee est celle qui est renvoyee a l'ecran.",
                    "Valeur affichee = valeur verifiee", "Relecture par l'agent Lint, avec un test dedie.")


# ------------------------------------------------------------------------ sortie

def trier():
    ordre = {BLOQUANT: 0, AVERT: 1, RELIRE: 2}
    return sorted(CONSTATS, key=lambda c: (ordre[c.gravite], c.regle, c.fichier, c.ligne))


def emplacement(c: Constat) -> str:
    return f"{c.fichier}:{c.ligne}" if c.ligne else c.fichier


def afficher_texte(root: Path, lot):
    cs = trier()
    nb = {g: sum(1 for c in cs if c.gravite == g) for g in (BLOQUANT, AVERT, RELIRE)}
    print(f"Scribo Lint (script v{VERSION_SCRIPT}) - depot : {root}" + (f" - lot {lot}" if lot else ""))
    print(f"Resume : {nb[BLOQUANT]} bloquant(s), {nb[AVERT]} avertissement(s), "
          f"{nb[RELIRE]} point(s) a relire, {len(NON_VERIFIABLES)} non verifiable(s)\n")
    for gravite, titre in ((BLOQUANT, "BLOQUANTS"), (AVERT, "AVERTISSEMENTS"), (RELIRE, "A RELIRE PAR L'AGENT LINT")):
        sel = [c for c in cs if c.gravite == gravite]
        if not sel:
            continue
        print(titre)
        for i, c in enumerate(sel, 1):
            print(f"  {i}. [{c.regle}] {emplacement(c)}")
            print(f"     {c.message}")
            print(f"     Invariant : {c.invariant}")
            print(f"     Correction : {c.correction}")
        print()
    if NON_VERIFIABLES:
        print("NON VERIFIABLES")
        for r, raison in NON_VERIFIABLES:
            print(f"  [{r}] {raison}")
        print()
    if REUSSIES:
        print("REGLES PASSEES")
        for r in sorted(REUSSIES):
            print(f"  [{r}] {REUSSIES[r]}")
        print()
    print("Verdict du script : " + ("REFUSE (au moins un constat bloquant)" if nb[BLOQUANT] else
                                    "aucun constat bloquant (la relecture reste a faire)"))


def afficher_md():
    print("| N° | Règle | Sévérité | Fichier et ligne | Constat | Invariant | Correction suggérée |")
    print("|---|---|---|---|---|---|---|")
    for i, c in enumerate(trier(), 1):
        gravite = {BLOQUANT: "Bloquant", AVERT: "Avertissement", RELIRE: "À relire"}[c.gravite]
        print(f"| {i} | {c.regle} | {gravite} | {emplacement(c)} | {c.message} | {c.invariant} | {c.correction} |")


def main():
    ap = argparse.ArgumentParser(description="Controle deterministe d'un lot Scribo")
    ap.add_argument("--root", default=None, help="racine du depot")
    ap.add_argument("--lot", default=None, help="numero du lot a controler, ex. 05")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--md", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve() if a.root else Path(__file__).resolve().parent.parent
    if not (root / "extracteur.py").exists():
        print(f"Depot Scribo introuvable dans {root} (extracteur.py absent).", file=sys.stderr)
        return 2
    if a.lot and not a.lot.isdigit():
        print("--lot attend un numero, par exemple 05.", file=sys.stderr)
        return 2
    regle_r01(root)
    regle_r03(root)
    regle_r04(root)
    regle_r05(root)
    regle_r06(root)
    regle_r07(root)
    regle_r08(root, a.lot)
    regle_r09(root)
    regle_r10(root)
    regle_r11(root)
    regle_r13_r02(root)
    if a.json:
        print(json.dumps({
            "script": VERSION_SCRIPT, "depot": str(root), "lot": a.lot,
            "constats": [asdict(c) for c in trier()],
            "non_verifiables": [{"regle": r, "raison": x} for r, x in NON_VERIFIABLES],
            "regles_passees": REUSSIES,
        }, ensure_ascii=False, indent=2))
    elif a.md:
        afficher_md()
    else:
        afficher_texte(root, a.lot)
    return 1 if any(c.gravite == BLOQUANT for c in CONSTATS) else 0


if __name__ == "__main__":
    sys.exit(main())
