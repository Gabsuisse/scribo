#!/usr/bin/env python3
"""
extracteur.py — serveur local d'extraction de documents.

Charge Mistral 7B via mlx-lm (même approche que Mistico), lit le document,
extrait les champs, puis recontrôle chaque valeur par des règles de calcul.

Lancement (recommandé, avec uv — installe Python + dépendances tout seul) :
    uv run extracteur.py
    → http://localhost:8000

Alternative (si Python 3.10+ est déjà installé) :
    python3 -m pip install mlx-lm pdfplumber ocrmac pymupdf
    python3 extracteur.py

Dépendances (déclarées dans pyproject.toml) :
    mlx-lm : inférence Mistral · pdfplumber : PDF texte ·
    ocrmac : OCR des images · pymupdf : rasterisation des PDF scannés
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


def _ocr_image(chemin):
    """OCR d'un fichier image via ocrmac (moteur Vision d'Apple)."""
    from ocrmac import ocrmac
    resultats = ocrmac.OCR(chemin, language_preference=["fr-FR", "en-US"]).recognize()
    return "\n".join(r[0] for r in resultats)


def lire_image(chemin):
    try:
        return _ocr_image(chemin)
    except ImportError:
        raise RuntimeError(
            "La lecture d'images demande ocrmac. Installez-le avec : "
            "python3 -m pip install ocrmac"
        )


def _ocr_pdf_scanne(chemin):
    """Rasterise chaque page d'un PDF scanné en image, puis l'OCR.
    Utilise PyMuPDF (fitz), pur-Python, pas de dépendance système."""
    import fitz  # PyMuPDF

    morceaux = []
    with fitz.open(chemin) as doc:
        for page in doc[:3]:  # 3 premières pages suffisent pour un RIB
            pix = page.get_pixmap(dpi=200)  # 200 dpi : bon compromis netteté/vitesse
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                pix.save(tmp.name)
                chemin_img = tmp.name
            try:
                morceaux.append(_ocr_image(chemin_img))
            finally:
                os.unlink(chemin_img)
    return "\n".join(morceaux)


def lire_document(chemin, nom):
    """Lit un document quel que soit son type, de façon transparente.
    PDF avec texte → lecture directe. PDF scanné ou image → OCR automatique.
    L'utilisateur n'a jamais à choisir : il dépose, on lui rend le texte."""
    if nom.lower().endswith(".pdf"):
        texte = lire_pdf(chemin)
        # assez de texte réel → PDF numérique, on le lit directement
        if len(re.sub(r"\s", "", texte)) > 40:
            return texte
        # sinon c'est un scan : on bascule sur l'OCR, sans rien demander
        try:
            texte_ocr = _ocr_pdf_scanne(chemin)
        except ImportError:
            raise RuntimeError(
                "Ce PDF est un scan ; sa lecture demande PyMuPDF et ocrmac. "
                "Installez-les avec : python3 -m pip install pymupdf ocrmac"
            )
        if len(re.sub(r"\s", "", texte_ocr)) > 20:
            return texte_ocr
        raise RuntimeError(
            "Document illisible : ni couche texte, ni caractères reconnus par l'OCR. "
            "Vérifiez que le document est net et bien cadré."
        )
    # tout le reste (png, jpg, jpeg, webp…) passe par l'OCR
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


CONSIGNE_PASSEPORT = """Tu extrais des champs d'un passeport.

Réponds UNIQUEMENT par un objet JSON, sans texte avant ni après, avec exactement ces clés :
{"nom": ..., "prenom": ..., "numero": ..., "nationalite": ..., "date_naissance": ..., "sexe": ..., "date_expiration": ..., "mrz_ligne1": ..., "mrz_ligne2": ...}

Règles strictes :
- Recopie uniquement ce qui est présent dans le texte. N'invente jamais une valeur.
- Si un champ est absent, mets null. Ne devine pas.
- nom : le nom de famille (surname), en majuscules.
- prenom : le ou les prénoms (given names), tels qu'écrits.
- numero : le numéro du passeport (passport number), lettres et chiffres.
- nationalite : le code ou le nom de la nationalité.
- date_naissance : au format AAAA-MM-JJ si possible.
- sexe : M, F ou X.
- date_expiration : au format AAAA-MM-JJ si possible.
- mrz_ligne1 et mrz_ligne2 : les DEUX lignes de la zone lisible par machine (MRZ), en bas du passeport, recopiées EXACTEMENT caractère par caractère, y compris tous les chevrons "<". Chaque ligne fait 44 caractères. Si tu ne vois pas la MRZ, mets null."""


def interroger(texte, consigne=CONSIGNE):
    from mlx_lm import stream_generate

    modele, tokenizer = charger_modele()
    messages = [
        {"role": "user", "content": consigne + "\n\nTexte du document :\n\n" + texte[:MAX_CARACTERES]},
    ]
    invite = tokenizer.apply_chat_template(messages, add_generation_prompt=True)

    morceaux = []
    for reponse in stream_generate(modele, tokenizer, invite, max_tokens=220):
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


# ─────────────────────────────────────────────────────────────
# Passeport — vérification par les clés de la MRZ (norme ICAO 9303)
# ─────────────────────────────────────────────────────────────

def _mrz_valeur(caractere):
    """Valeur d'un caractère MRZ : chiffres = valeur, A-Z = 10..35, '<' = 0."""
    if caractere.isdigit():
        return int(caractere)
    if caractere == "<":
        return 0
    if "A" <= caractere <= "Z":
        return ord(caractere) - 55  # A=10, B=11, … Z=35
    return 0


def mrz_cle(champ):
    """Calcule la clé de contrôle d'un champ MRZ (pondération 7-3-1)."""
    poids = [7, 3, 1]
    total = sum(_mrz_valeur(c) * poids[i % 3] for i, c in enumerate(champ))
    return total % 10


def mrz_champ_valide(champ, cle_attendue):
    """Vrai si la clé de contrôle du champ correspond à la clé lue."""
    if not champ or cle_attendue is None or cle_attendue == "":
        return None
    try:
        return mrz_cle(champ) == int(cle_attendue)
    except (ValueError, TypeError):
        return None


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
# Détection du type de document (hybride : le document réel prime)
# ─────────────────────────────────────────────────────────────

def detecter_type(texte, type_indique=None):
    """Détermine le type réel du document. Le contenu prime sur type_indique.
    Retourne 'passeport' ou 'rib'."""
    t = texte.upper()
    # signature MRZ passeport : "P<" suivi du code pays (3 lettres), ou une
    # séquence typique de chevrons (au moins 6 d'affilée = zone MRZ)
    a_mrz = bool(re.search(r"P<[A-Z<]{3}", t) or re.search(r"<{6,}", t))
    # signature IBAN français
    a_iban = bool(re.search(r"\bFR\d{2}[\sA-Z0-9]{18,}", t))

    if a_mrz and not a_iban:
        return "passeport"
    if a_iban and not a_mrz:
        return "rib"
    # ambigu ou aucun signal fort → on suit l'indication de l'app si fournie
    if type_indique in ("passeport", "rib"):
        return type_indique
    # dernier recours : MRZ prioritaire, sinon RIB (comportement historique)
    return "passeport" if a_mrz else "rib"


def _mrz_date_vers_iso(aammjj, naissance=True):
    """Convertit une date MRZ 'AAMMJJ' (année sur 2 chiffres) en 'AAAA-MM-JJ'.
    Règle du siècle : une date de naissance ne peut pas être dans le futur.
    Pour une date d'expiration, on reste dans une fenêtre proche du présent."""
    import datetime
    if not aammjj or len(aammjj) != 6 or not aammjj.isdigit():
        return None
    aa, mm, jj = int(aammjj[0:2]), int(aammjj[2:4]), int(aammjj[4:6])
    if not (1 <= mm <= 12 and 1 <= jj <= 31):
        return None
    annee_courante = datetime.date.today().year
    deux_derniers = annee_courante % 100
    if naissance:
        # naissance jamais dans le futur : si "aa" > année courante (2 chiffres),
        # c'est le siècle précédent ; sinon le siècle courant.
        siecle = (annee_courante // 100) if aa <= deux_derniers else (annee_courante // 100 - 1)
    else:
        # expiration : généralement dans le futur proche → siècle courant,
        # sauf si ça donne une date très ancienne.
        siecle = annee_courante // 100
        if siecle * 100 + aa < annee_courante - 10:
            siecle += 1
    annee = siecle * 100 + aa
    try:
        datetime.date(annee, mm, jj)  # validation
    except ValueError:
        return None
    return f"{annee:04d}-{mm:02d}-{jj:02d}"


def _memes_dates(a, b):
    """Compare deux dates ISO en tolérant les formats (AAAA-MM-JJ vs AAAA/MM/JJ…)."""
    if not a or not b:
        return None
    na = re.sub(r"[^0-9]", "", str(a))
    nb = re.sub(r"[^0-9]", "", str(b))
    if len(na) != 8 or len(nb) != 8:
        return None
    return na == nb


def _memes_valeurs(a, b):
    """Compare deux valeurs texte en ignorant casse, espaces et chevrons MRZ."""
    if not a or not b:
        return None
    na = re.sub(r"[^A-Z0-9]", "", str(a).upper())
    nb = re.sub(r"[^A-Z0-9]", "", str(b).upper())
    if not na or not nb:
        return None
    return na == nb


def _mrz_parse_noms(l1):
    """Extrait nom et prénoms de la ligne 1 d'une MRZ TD3 (norme ICAO 9303).
    Format : P<PAYS NOM<<PRENOM1<PRENOM2<<<...
    '<<' sépare le nom des prénoms ; '<' simple = espace à l'intérieur.
    Universel : identique sur tous les passeports du monde."""
    if not l1 or len(l1) < 5:
        return None, None
    # on saute 'P' (type, position 0), le caractère 1 (souvent '<'), et le code pays (2-4)
    zone_noms = l1[5:]
    # séparation nom / prénoms sur le premier '<<'
    if "<<" in zone_noms:
        partie_nom, partie_prenoms = zone_noms.split("<<", 1)
    else:
        partie_nom, partie_prenoms = zone_noms, ""

    def nettoyer(bloc):
        # '<' simple = espace ; on retire les '<' de remplissage en fin
        mots = [m for m in bloc.split("<") if m]
        return " ".join(mots) if mots else None

    nom = nettoyer(partie_nom)
    prenoms = nettoyer(partie_prenoms)
    return nom, prenoms


def construire_passeport(brut, source):
    l1 = str(brut.get("mrz_ligne1") or "").upper().replace(" ", "")
    l2 = str(brut.get("mrz_ligne2") or "").upper().replace(" ", "")

    # La MRZ passeport (TD3) : ligne 2 contient les clés de contrôle.
    # Positions (0-indexées) sur la ligne 2 de 44 caractères :
    #  0-8   numéro de passeport   | 9    clé du numéro
    #  13-18 date de naissance     | 19   clé de la date de naissance
    #  21-26 date d'expiration     | 27   clé de la date d'expiration
    num_ok = naiss_ok = exp_ok = None
    # valeurs DÉRIVÉES de la MRZ = source primaire de TOUS les champs (universel, tous pays)
    mrz_num = mrz_naiss = mrz_exp = mrz_sexe = mrz_nat = None
    if len(l2) >= 28:
        num_ok = mrz_champ_valide(l2[0:9], l2[9])
        naiss_ok = mrz_champ_valide(l2[13:19], l2[19])
        exp_ok = mrz_champ_valide(l2[21:27], l2[27])
        mrz_num = l2[0:9].replace("<", "") or None
        mrz_nat = l2[10:13].replace("<", "") or None
        mrz_naiss = _mrz_date_vers_iso(l2[13:19], naissance=True)
        mrz_exp = _mrz_date_vers_iso(l2[21:27], naissance=False)
        sexe_c = l2[20:21]
        mrz_sexe = sexe_c if sexe_c in ("M", "F") else ("X" if sexe_c == "<" else None)

    # nom + prénoms depuis la ligne 1 (règle NOM<<PRENOMS, universelle)
    mrz_nom, mrz_prenoms = _mrz_parse_noms(l1)

    def champ_mrz(val_mrz, val_visuel, cle_ok=None, est_date=False):
        """Champ dont la MRZ est la source primaire. Le visuel n'est qu'un
        bonus SILENCIEUX : il augmente la confiance s'il concorde, mais son
        absence ou sa divergence ne pénalise PAS et n'affiche aucune alerte.
        Retourne (valeur, tag, score)."""
        # si la MRZ n'a rien, on retombe sur le visuel (repli)
        if not val_mrz:
            v = val_visuel
            return v, None, confiance(v, source)
        # clé de contrôle explicitement fausse → seul cas où l'on alerte
        if cle_ok is False:
            return val_mrz, "Clé MRZ invalide — à corriger", 55
        # concordance visuelle (bonus silencieux)
        if val_visuel:
            memes = _memes_dates(val_mrz, val_visuel) if est_date else _memes_valeurs(val_mrz, val_visuel)
        else:
            memes = None
        # la MRZ fait foi : valeur MRZ, haute confiance
        if cle_ok is True:
            # champ vérifié par sa clé de contrôle
            tag = "Vérifié · MRZ + document" if memes is True else "Clé MRZ vérifiée"
            return val_mrz, tag, 99
        # champ MRZ sans clé propre (nom, prénoms, nationalité, sexe)
        if memes is True:
            return val_mrz, "Lu dans la MRZ · confirmé", 96
        return val_mrz, "Lu dans la MRZ", 90

    v_nom, t_nom, s_nom = champ_mrz(mrz_nom, brut.get("nom"))
    v_pre, t_pre, s_pre = champ_mrz(mrz_prenoms, brut.get("prenom"))
    v_num, t_num, s_num = champ_mrz(mrz_num, brut.get("numero"), cle_ok=num_ok)
    v_nat, t_nat, s_nat = champ_mrz(mrz_nat, brut.get("nationalite"))
    v_nai, t_nai, s_nai = champ_mrz(mrz_naiss, brut.get("date_naissance"), cle_ok=naiss_ok, est_date=True)
    v_sex, t_sex, s_sex = champ_mrz(mrz_sexe, brut.get("sexe"))
    v_exp, t_exp, s_exp = champ_mrz(mrz_exp, brut.get("date_expiration"), cle_ok=exp_ok, est_date=True)

    champs = [
        {"cle": "nom", "nom": "Nom", "valeur": v_nom, "score": s_nom, "src": t_nom},
        {"cle": "prenom", "nom": "Prénom(s)", "valeur": v_pre, "score": s_pre, "src": t_pre},
        {"cle": "numero", "nom": "N° de passeport", "valeur": v_num, "score": s_num, "src": t_num},
        {"cle": "nationalite", "nom": "Nationalité", "valeur": v_nat, "score": s_nat, "src": t_nat},
        {"cle": "date_naissance", "nom": "Date de naissance", "valeur": v_nai, "score": s_nai, "src": t_nai},
        {"cle": "sexe", "nom": "Sexe", "valeur": v_sex, "score": s_sex, "src": t_sex},
        {"cle": "date_expiration", "nom": "Date d'expiration", "valeur": v_exp, "score": s_exp, "src": t_exp},
    ]

    # bilan global : vérifié si les clés de contrôle présentes tombent toutes juste
    mrz_ok = None
    controles = [num_ok, naiss_ok, exp_ok]
    if any(c is not None for c in controles):
        mrz_ok = all(c for c in controles if c is not None)

    return {"champs": champs, "type": "passeport", "mrzOk": mrz_ok,
            "texte": source[:4000], "modele": MODELE}


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
            print(f"  {nom} — {len(texte)} caractères lus…")
            # type indiqué par l'app (facultatif), mais le document réel prime
            type_indique = self.headers.get("X-Type-Document")  # "rib" | "passeport" | None
            type_reel = detecter_type(texte, type_indique)
            print(f"  Type indiqué : {type_indique or '—'} · type détecté : {type_reel}")
            if type_reel == "passeport":
                brut = extraire_json(interroger(texte, CONSIGNE_PASSEPORT))
                self._json(200, construire_passeport(brut, texte))
            else:
                brut = extraire_json(interroger(texte, CONSIGNE))
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
