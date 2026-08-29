# Scribo — Documentation technique (`agent.md`)

> Extraction locale et souveraine de données de documents.
> **Thèse produit : « le modèle propose, l'arithmétique dispose. »**
> Le modèle extrait, des règles de calcul déterministes vérifient, rien ne quitte la machine.

Date : 29/08/2026
Lot : n°2
Version produit : v0.5.0

---

---

## 1. Objectif du projet

Scribo lit un document (RIB ou passeport), en extrait les champs structurés, **recontrôle chaque valeur par des règles de calcul déterministes**, puis les restitue prêts à pré-remplir un formulaire (copie champ par champ, ou export JSON).

Le différenciateur central est la **souveraineté** : tout se passe en local, sur la machine de l'utilisateur. Aucune donnée n'est envoyée sur un serveur tiers. On peut couper le Wi-Fi et vérifier.

Le second différenciateur est la **fiabilité par le calcul** : une valeur validée par une clé de contrôle (mod-97 pour l'IBAN, clés ICAO 9303 pour la MRZ) ne peut pas être une hallucination du modèle.

---

## 2. Architecture technique

### Vue d'ensemble

Scribo a **deux morceaux** qui communiquent en local :

1. **Un serveur Python** (`extracteur.py`) qui charge le modèle, lit les documents, extrait et vérifie. Il sert aussi la page web de l'interface.
2. **Une interface web** (`extractorultimator.html`) — un fichier autonome HTML/CSS/JS vanilla, servi par le serveur Python à `http://localhost:8000`.

Le front (JS) parle au back (Python) via des requêtes HTTP locales (`/extract`, `/statut`). Même origine, aucun appel externe.

Il existe par ailleurs une **landing page** de présentation (`index.html`, dupliquée en `scribo.html`), hébergée séparément (Scaleway Object Storage), avec une démo scénarisée sur données fictives.

### Stack

- **Inférence** : Mistral 7B (`mlx-community/Mistral-7B-Instruct-v0.3-4bit`) via **MLX** (bibliothèque Apple Silicon). **Contrainte forte : Mac Apple Silicon uniquement** (M1+). Pas de Windows, Linux, ni Mac Intel.
- **Lecture documents** : `pdfplumber` (PDF texte), `ocrmac` (OCR natif via le moteur Vision d'Apple, images), `pymupdf`/`fitz` (rasterisation des PDF scannés pour OCR).
- **Serveur** : `http.server` / `socketserver` de la stdlib Python (aucun framework).
- **Front** : HTML/CSS/JavaScript vanilla, fichier unique, aucune chaîne de build.
- **Installation** : `uv` (gère Python + dépendances en une commande), déclarée dans `pyproject.toml`.

### Structure des fichiers

```
scribo_repo/
├── extracteur.py            # serveur Python : modèle, lecture, extraction, vérification
├── extractorultimator.html  # interface de l'app (servie par le serveur)
├── pyproject.toml           # dépendances + version Python (pour uv)
├── README.md                # présentation + instructions de lancement
├── index.html / scribo.html # landing page (hébergée sur Scaleway, hors app)
└── docs/banner.png          # bannière du repo GitHub
```

### Dépendances clés (`pyproject.toml`)

`mlx-lm`, `pdfplumber`, `ocrmac`, `pymupdf`. Python >= 3.10.

### Lancement

Recommandé : `uv run extracteur.py` (uv installe Python + dépendances automatiquement, dans un `.venv` isolé). Puis ouvrir `http://localhost:8000/extractorultimator.html`.
Alternative : `pip install mlx-lm pdfplumber ocrmac pymupdf` puis `python3 extracteur.py`.

---

## 3. Logique métier et règles fonctionnelles — App locale

### Lecture des documents (transparente)

`lire_document()` route selon le type de fichier, sans que l'utilisateur choisisse :
- PDF avec couche texte → lecture directe (`pdfplumber`).
- PDF scanné (peu de texte réel) → rasterisation (`pymupdf`, 200 dpi) puis OCR.
- Image (png/jpg/webp…) → OCR direct (`ocrmac`).

Le document temporaire est **supprimé immédiatement** après traitement (`os.unlink`), jamais conservé.

### Détection du type de document (hybride)

`detecter_type(texte, type_indique)` : **le contenu réel du document prime toujours** sur le type indiqué par l'app.
- Signature MRZ (`P<` + code pays, ou séquence de `<<<<<<`) → passeport.
- Signature IBAN français (`FR` + 2 chiffres + suite) → RIB.
- Ambigu → on suit l'indication de l'app (en-tête `X-Type-Document`) en secours.

L'app envoie le type choisi par l'utilisateur (clic sur une card), mais si quelqu'un dépose un passeport en ayant cliqué « RIB », le passeport est quand même correctement traité.

### RIB — extraction et vérification

- Le modèle extrait : titulaire, IBAN, BIC, banque, domiciliation.
- **Vérification IBAN** : clé mod-97 (`iban_valide`). Un IBAN qui passe la clé est fiable.
- **Dérivation** : une fois l'IBAN validé, le code banque, le code guichet, le numéro de compte et la clé RIB sont **découpés depuis l'IBAN** (`decomposer_iban`), pas devinés → score 100.
- `nettoyer_domiciliation` : filet de sécurité qui retire l'adresse du titulaire, téléphones et codes postaux parfois aspirés dans le champ domiciliation.

### Passeport — la MRZ comme source primaire universelle

**Principe clé (appris à l'usage) : la MRZ est la source primaire de TOUS les champs, pas le scan visuel.**

La MRZ (Machine Readable Zone, deux lignes en bas du passeport) suit la norme **ICAO 9303**, **identique sur tous les passeports du monde**. Contrairement à la mise en page visuelle qui varie par pays (ce qui faisait échouer l'extraction sur, p. ex., un passeport hollandais), la MRZ est positionnelle et universelle.

Le pipeline passeport :
1. Le modèle recopie les deux lignes MRZ (et tente une lecture visuelle des champs).
2. **Tous les champs sont dérivés de la MRZ** :
   - **Ligne 1** : nom et prénoms (`_mrz_parse_noms`), règle `NOM<<PRENOM1<PRENOM2` (`<<` sépare nom/prénoms, `<` simple = espace). → règle définitivement la confusion nom/prénom.
   - **Ligne 2** (positions fixes TD3) : numéro (0-8) + clé (9), nationalité (10-12), date de naissance (13-18) + clé (19), sexe (20), expiration (21-26) + clé (27).
3. **Vérification par les clés de contrôle** ICAO (`mrz_cle`, pondération 7-3-1 ; `mrz_champ_valide`). Validé contre l'exemple officiel de la spec.
4. **Le scan visuel du modèle n'est qu'un bonus SILENCIEUX** : s'il concorde avec la MRZ → petit bonus de confiance (« confirmé ») ; s'il diverge ou est absent → **aucune pénalité, aucune alerte** (la MRZ fait foi).
5. **Repli** : si la MRZ est illisible (scan trop mauvais), on retombe sur la lecture visuelle du modèle, sans tag « vérifié ».

**Règle du siècle** (`_mrz_date_vers_iso`) : l'année MRZ est sur 2 chiffres. Pour une date de naissance, on choisit le siècle tel que la date ne soit jamais dans le futur (« 23 » → 2023, « 95 » → 1995). Pour l'expiration, siècle courant par défaut.

### Scoring de confiance

- Champ MRZ vérifié par sa clé de contrôle → **99**.
- Champ MRZ sans clé propre (nom, prénoms, nationalité, sexe), confirmé par le visuel → **96** ; non confirmé → **90**.
- Clé de contrôle explicitement fausse → **55** + tag « Clé MRZ invalide ».
- Repli visuel (pas de MRZ) → `confiance()` classique : 50 base, +30 si la valeur apparaît telle quelle dans le texte source, +20 si elle passe son contrôle de format.

### États de l'interface

Les états visibles de l'app locale sont énumérés et maquettés dans le canvas
userflow décrit dans `design.md` (§ 2 bis) : statut serveur (chargement / prêt /
injoignable), modale d'extraction (dépôt vide, fichier prêt, scan, résultats),
et les états limites (format refusé, clé MRZ invalide, serveur injoignable).
Toute nouvelle famille de documents activée dans `CATALOGUE` doit ajouter ses
artboards à ce canvas.

### Réponses du serveur

- `GET /statut` → `{pret, modele, charge}` (`charge` = modèle chargé en mémoire).
- `POST /extract` (corps = fichier, en-têtes `X-Nom-Fichier`, `X-Type-Document`) → `{champs:[{cle,nom,valeur,score,src}], type, ibanOk|mrzOk, texte, modele}`.

---

## 3 bis. Landing page (site vitrine)

Volet distinct de l'app : un site de présentation, sans lien fonctionnel avec le
serveur Python.

- **Fichiers** : `index.html` (dupliqué à l'identique en `scribo.html`).
- **Hébergement** : Scaleway Object Storage (bucket `scribo-demo`, région fr-par),
  URL `https://scribo-demo.s3-website.fr-par.scw.cloud/`. Mise à jour = uploader `index.html`.
- **Technique** : HTML/CSS/JS vanilla, fichier unique, aucune chaîne de build.
  Bilingue FR/EN (dictionnaires i18n + `data-i18n`), dark/light mode avec persistance
  (localStorage).
- **Contenu** : hero, section « Principe » (data does not travel), **démo scénarisée
  sur données 100 % fictives** (aucun modèle appelé, aucune donnée transmise), section
  technique « le modèle propose, l'arithmétique dispose », frise défilante, footer légal.
- **Indépendance** : la landing ne communique jamais avec le serveur local ; sa démo
  est scriptée. Elle sert uniquement à présenter le projet et renvoyer vers le repo GitHub.

---

## 4. Décisions techniques et justifications

- **MLX (Apple Silicon only)** plutôt qu'une réécriture llama.cpp : l'écosystème IA locale (MLX, mlx-lm, modèles quantifiés) est en Python et optimisé pour la puce. La portabilité est notée comme évolution future.
- **`uv` pour l'installation** plutôt que pip seul ou un `.app` : `uv` installe Python lui-même si absent, en une commande, dans un `.venv` isolé. Résout le cas « l'utilisateur n'a pas Python ». Le `.app` double-clic (packaging + signature Apple) est jugé trop lourd avant l'objectif principal.
- **Front vanilla, fichier unique, pas de Tailwind/build** : la simplicité de lancement (`uv run`, un fichier servi) est un atout produit. Une chaîne de build front casserait cette promesse. Choix assumé et cohérent avec la nature locale du projet.
- **MRZ = source primaire universelle** (et non simple validateur) : règle la confusion nom/prénom et l'échec sur les passeports étrangers sans avoir à fournir un exemple par pays. Généralisation de la thèse : « lire depuis la structure normalisée, confirmer par le visuel, ne jamais deviner ».
- **Détection de type hybride, document réel prioritaire** : robustesse (l'utilisateur peut se tromper de card) sans sacrifier la fiabilité.

---

## 5. Points d'attention et contraintes connues

- **Apple Silicon obligatoire.** Ne fonctionne pas ailleurs (limite intrinsèque de MLX).
- **Dépend de la qualité de l'OCR sur la MRZ.** Si un scan est si mauvais que la MRZ elle-même est corrompue à l'OCR, la dérivation lira une valeur fausse. Les clés de contrôle attrapent la plupart de ces cas ; le repli visuel gère l'absence de MRZ.
- **Le modèle doit recopier fidèlement les deux lignes MRZ.** Tout le pipeline passeport en dépend. La MRZ passe généralement mieux à l'OCR que le reste (conçue pour la lecture machine).
- **Données de démo strictement fictives.** Passeport et RIB d'exemple doivent être inventés (jamais un vrai document). Scribo est une démonstration technique, pas un produit certifié (aucune certification HDS/SecNumCloud revendiquée).
- **Modèle non exécutable hors environnement cible** : la logique est validée par simulation/tests ; les tests réels (extraction sur vrais documents) se font sur un Mac Apple Silicon.

---

## 6. Ce qui reste à faire / pistes

- Tester en conditions réelles l'extraction passeport multi-pays (le hollandais notamment) et le cas MRZ dégradée.
- Mettre l'exemple passeport fictif sur la démo de la landing (remplacer un exemple RIB). MRZ fictive valide déjà générée (SPECIMEN/MARIE, FRA).
- Évolution possible : packaging `.app` (double-clic, sans terminal) pour un usage grand public — nécessite signature/notarisation Apple.
- Évolution possible : portabilité hors Apple Silicon (llama.cpp) si besoin d'élargir la cible.
- Valider le nom « Scribo » (INPI + domaine) avant un éventuel domaine personnalisé.

---

## Historique

- v0.5.0 (Lot 2, 29/08/2026) : deux correctifs CSS dans
  `extractorultimator.html` — `var(--encre)` (non déclarée) remplacée par
  `var(--d-txt)`, et rayons ramenés à 6px sur `.cta`, `.tout-copier`, `.dl-json`,
  `.lang-trigger`. Aucun changement fonctionnel. Le design system est désormais
  porté par un fichier Figma décrit dans `design.md` § 2 ter.
- v0.4.0 (Lot 1, 29/08/2026) : ajout du bloc méta ; ajout d'une section
  « États de l'interface » renvoyant au canvas userflow documenté dans `design.md`.
- v0.2.0 (27/08/2026) : structuration Landing / App locale — ajout d'une section
  dédiée à la landing (hébergement Scaleway, démo scriptée), la section logique métier
  précisée « App locale ».
- v0.1.0 (août 2026) : première version de `agent.md`. État du projet : RIB + passeport fonctionnels, install `uv`, OCR natif, MRZ comme source primaire universelle.
