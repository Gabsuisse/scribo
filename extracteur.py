#!/usr/bin/env python3
"""
extracteur.py — serveur local d'extraction de documents.

Charge Mistral 7B via mlx-lm (même approche que Mistico), lit le document,
extrait les champs, puis recontrôle chaque valeur par des règles de calcul.

Lancement :
    python3 extracteur.py
    → http://localhost:8000

Dépendances :
    pip install mlx-lm pdfplumber
    pip install ocrmac          (facultatif, pour les images et PDF scannés)
"""

import http.server
import json
import os
import re
import socketserver
import tempfile
import threading

# ─────────────────────────────────────────────────────────────
# Réglages
# ─────────────────────────────────────────────────────────────
MODELE = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"  # ← à aligner sur Mistico
PORT = 8000
PAGE = "extractorultimator.html"
MAX_CARACTERES = 6000

_modele = None
_tokenizer = None
_verrou = threading.Lock()


def charger_modele():
    """Charge le modèle une seule fois, au premier appel."""
    global _modele, _tokenizer
    with _verrou:
        if _modele is None:
            from mlx_lm import load
            print(f"  Chargement de {MODELE} …")
            _modele, _tokenizer = load(MODELE)
            print("  Modèle prêt.")
    return _modele, _tokenizer


# ─────────────────────────────────────────────────────────────
# Lecture des documents
# ─────────────────────────────────────────────────────────────
def lire_pdf(chemin):
    import pdfplumber
    with pdfplumber.open(chemin) as pdf:
        return "\n".join((p.extract_text() or "") for p in pdf.pages[:3])


def lire_image(chemin):
    try:
        from ocrmac import ocrmac
    except ImportError:
        raise RuntimeError(
            "La lecture d'images demande ocrmac. Installez-le avec "
            "pip install ocrmac, ou déposez un PDF."
        )
    resultats = ocrmac.OCR(chemin, language_preference=["fr-FR"]).recognize()
    return "\n".join(r[0] for r in resultats)


def lire_document(chemin, nom):
    if nom.lower().endswith(".pdf"):
        texte = lire_pdf(chemin)
        if len(re.sub(r"\s", "", texte)) > 40:
            return texte
        raise RuntimeError(
            "Ce PDF ne contient pas de couche texte, c'est un scan. "
            "Exportez-le en image puis redéposez-le, ou utilisez le PDF d'origine."
        )
    return lire_image(chemin)


# ─────────────────────────────────────────────────────────────
# Appel du modèle
# ─────────────────────────────────────────────────────────────
CONSIGNE = """Tu extrais des champs d'un relevé d'identité bancaire français (RIB).

Réponds UNIQUEMENT par un objet JSON, sans texte avant ni après, avec exactement ces clés :
{"titulaire": ..., "iban": ..., "bic": ..., "banque": ..., "domiciliation": ...}

Règles strictes :
- Recopie uniquement ce qui est présent dans le texte. N'invente jamais une valeur.
- Si un champ est absent du texte, mets null. Ne devine pas.
- iban : lettres et chiffres collés, sans espaces, en majuscules.
- bic : le code BIC/SWIFT, 8 ou 11 caractères, en majuscules.
- titulaire : le nom du titulaire du compte, tel qu'écrit. Ignore son adresse postale.
- banque : le nom de l'établissement (ex. LA BANQUE POSTALE, CREDIT AGRICOLE).
- domiciliation : UNIQUEMENT le nom ou la ville de l'agence bancaire (souvent une seule ligne courte, ex. "PARIS OPERA" ou "SAINT MANDE"). N'y mets PAS l'adresse du titulaire, ni un numéro de téléphone, ni le code postal du client. En cas de doute, prends le libellé le plus court situé près du mot "Domiciliation"."""


def interroger(texte):
    from mlx_lm import stream_generate

    modele, tokenizer = charger_modele()
    messages = [
        {"role": "user", "content": CONSIGNE + "\n\nTexte du document :\n\n" + texte[:MAX_CARACTERES]},
    ]
    invite = tokenizer.apply_chat_template(messages, add_generation_prompt=True)

    morceaux = []
    for reponse in stream_generate(modele, tokenizer, invite, max_tokens=160):
        morceaux.append(getattr(reponse, "text", reponse))
    return "".join(morceaux)


def extraire_json(brut):
    """Récupère le premier objet JSON de la réponse, même entouré de texte."""
    brut = brut.strip()
    brut = re.sub(r"^```(?:json)?|```$", "", brut, flags=re.MULTILINE).strip()
    debut = brut.find("{")
    if debut == -1:
        raise ValueError("aucun JSON dans la réponse du modèle")
    profondeur = 0
    for i, c in enumerate(brut[debut:], debut):
        if c == "{":
            profondeur += 1
        elif c == "}":
            profondeur -= 1
            if profondeur == 0:
                return json.loads(brut[debut:i + 1])
    raise ValueError("JSON incomplet dans la réponse du modèle")


# ─────────────────────────────────────────────────────────────
# Contrôles déterministes
# ─────────────────────────────────────────────────────────────
def nettoyer_domiciliation(valeur):
    """Retire l'adresse du titulaire, les téléphones et codes postaux
    parfois aspirés dans le champ domiciliation par le modèle.
    Filet de sécurité : la consigne reste la première ligne de défense."""
    if not valeur:
        return valeur
    t = str(valeur).strip()
    # coupe à partir d'un numéro de téléphone (TEL, ou 10 chiffres groupés)
    t = re.split(r"\bT[ÉE]L\b|\b(?:\d[\s.]?){10}\b", t, flags=re.IGNORECASE)[0]
    # coupe au premier type de voie : le nom d'agence est avant, l'adresse après
    t = re.split(
        r"\b\d{1,4}\s+(?:RUE|AV(?:E|ENUE)?|BD|BOULEVARD|ALL[ÉE]E|IMPASSE|"
        r"PLACE|CHEMIN|ROUTE|QUAI|COURS)\b",
        t, flags=re.IGNORECASE)[0]
    # sinon, coupe au deuxième code postal (le 1er suffit à situer l'agence)
    cps = list(re.finditer(r"\b\d{5}\b", t))
    if len(cps) > 1:
        t = t[:cps[1].start()]
    return re.sub(r"\s{2,}", " ", t).strip(" ,-").strip() or None


def normaliser(v):
    return re.sub(r"[^A-Z0-9]", "", str(v or "").upper())


def iban_valide(iban):
    v = normaliser(iban)
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", v):
        return False
    perm = v[4:] + v[:4]
    nombre = "".join(str(ord(c) - 55) if c.isalpha() else c for c in perm)
    return int(nombre) % 97 == 1


def bic_valide(bic):
    return bool(re.fullmatch(r"[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?", normaliser(bic)))


def decomposer_iban(iban):
    v = normaliser(iban)
    if not v.startswith("FR") or len(v) != 27:
        return None
    return {
        "code_banque": v[4:9],
        "code_guichet": v[9:14],
        "numero_compte": v[14:25],
        "cle_rib": v[25:27],
    }


def confiance(valeur, source, controle=None):
    if not valeur:
        return 0
    score = 50
    n, src = normaliser(valeur), normaliser(source)
    if len(n) > 2 and n in src:
        score += 30
    if controle is True:
        score += 20
    elif controle is False:
        score -= 25
    return max(5, min(99, score))


def construire(brut, source):
    iban = normaliser(brut.get("iban")) or None
    iban_ok = iban_valide(iban) if iban else None
    bic_ok = bic_valide(brut.get("bic")) if brut.get("bic") else None
    parts = decomposer_iban(iban) if iban_ok else None

    domiciliation = nettoyer_domiciliation(brut.get("domiciliation"))

    champs = [
        {"cle": "titulaire", "nom": "Titulaire du compte",
         "valeur": brut.get("titulaire"),
         "score": confiance(brut.get("titulaire"), source), "src": None},

        {"cle": "iban", "nom": "IBAN",
         "valeur": " ".join(iban[i:i + 4] for i in range(0, len(iban), 4)) if iban else None,
         "score": confiance(iban, source, iban_ok),
         "src": "Clé mod-97 vérifiée" if iban_ok else
                ("Clé mod-97 invalide — à corriger" if iban_ok is False else None)},

        {"cle": "bic", "nom": "BIC / SWIFT",
         "valeur": normaliser(brut.get("bic")) or None,
         "score": confiance(brut.get("bic"), source, bic_ok),
         "src": "Format BIC inattendu" if bic_ok is False else None},

        {"cle": "banque", "nom": "Établissement",
         "valeur": brut.get("banque"),
         "score": confiance(brut.get("banque"), source), "src": None},

        {"cle": "domiciliation", "nom": "Domiciliation",
         "valeur": domiciliation,
         "score": confiance(domiciliation, source), "src": None},
    ]

    if parts:
        libelles = {
            "code_banque": "Code banque", "code_guichet": "Code guichet",
            "numero_compte": "Numéro de compte", "cle_rib": "Clé RIB",
        }
        for cle, valeur in parts.items():
            champs.append({"cle": cle, "nom": libelles[cle], "valeur": valeur,
                           "score": 100, "src": "Calculé depuis l'IBAN"})

    return {"champs": champs, "ibanOk": iban_ok, "texte": source[:4000], "modele": MODELE}


# ─────────────────────────────────────────────────────────────
# Serveur
# ─────────────────────────────────────────────────────────────
class Serveur(http.server.SimpleHTTPRequestHandler):

    def _json(self, code, charge):
        corps = json.dumps(charge, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def do_GET(self):
        if self.path.startswith("/statut"):
            return self._json(200, {"pret": True, "modele": MODELE,
                                    "charge": _modele is not None})
        if self.path in ("/", ""):
            self.path = "/" + PAGE
        return super().do_GET()

    def do_POST(self):
        if not self.path.startswith("/extract"):
            return self._json(404, {"erreur": "route inconnue"})

        nom = self.headers.get("X-Nom-Fichier", "document.pdf")
        taille = int(self.headers.get("Content-Length", 0))
        if taille == 0:
            return self._json(400, {"erreur": "fichier vide"})

        donnees = self.rfile.read(taille)
        suffixe = os.path.splitext(nom)[1] or ".pdf"

        with tempfile.NamedTemporaryFile(suffix=suffixe, delete=False) as f:
            f.write(donnees)
            chemin = f.name

        try:
            texte = lire_document(chemin, nom)
            print(f"  {nom} — {len(texte)} caractères lus, appel du modèle…")
            reponse = interroger(texte)
            brut = extraire_json(reponse)
            self._json(200, construire(brut, texte))
        except Exception as e:
            print(f"  Échec : {e}")
            self._json(422, {"erreur": str(e)})
        finally:
            os.unlink(chemin)  # le document n'est jamais conservé

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists(PAGE):
        print(f"  ⚠  {PAGE} est introuvable dans ce dossier.")
    socketserver.TCPServer.allow_reuse_address = True

    # préchauffage : on charge le modèle en tâche de fond dès le démarrage,
    # pendant que l'utilisateur ouvre le navigateur et prépare son fichier
    threading.Thread(target=charger_modele, daemon=True).start()

    with socketserver.TCPServer(("127.0.0.1", PORT), Serveur) as httpd:
        print(f"\n  extractorultimator → http://localhost:{PORT}")
        print(f"  Modèle : {MODELE} (chargé au premier document)")
        print("  Ctrl+C pour arrêter.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Arrêté.")
