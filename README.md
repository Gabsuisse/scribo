<a name="english"></a>
<p align="center">
  <img src="docs/banner.png" alt="Scribo — sovereign document extraction, Mistral 7B running locally" width="100%">
</p>

<p align="center">
  <strong>Field extraction from documents, without any data ever leaving the machine.</strong><br>
  Mistral 7B runs locally via MLX · values are verified by computation, not just generated.
</p>

<p align="center">
  <strong>English</strong> · <a href="#-français">Français</a>
</p>

<p align="center">
  <a href="#-run-it-locally">Run it locally</a> ·
  <a href="#-the-product-problem">The problem</a> ·
  <a href="#-the-architecture">Architecture</a> ·
  <a href="#-technical-decisions">Decisions</a> ·
  <a href="#-acknowledged-limits">Limits</a>
</p>

---

## In one sentence

Scribo reads a document (a French bank details slip — "RIB" — to start with), extracts the useful fields, **re-checks every value with a computational rule**, and makes them ready to paste into a form — all while running **entirely on the user's machine**, with no network call.

It's a product prototype: it works end to end, but it was deliberately kept simple to stay readable. This README explains the *product reasoning* as much as the code.

---

## ⚡ Run it locally

> ⚠️ **Platform: Apple Silicon Mac only** (M1, M2, M3 or newer chip).
> Scribo **does not run** on Windows, Linux, or Intel Macs, because its inference engine relies on **MLX**, Apple's chip-specific library. A portable version (via llama.cpp) may be considered later.

Scribo installs with **[uv](https://docs.astral.sh/uv/)**, which handles everything for you: it installs the right Python version if it's missing, creates an isolated environment and downloads the dependencies — all automatically. **No need to have Python beforehand.**

**1. Install `uv`** (once, if you don't already have it):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. Get Scribo**, either way:

```bash
# with git
git clone https://github.com/Gabsuisse/scribo.git
cd scribo
```

*Or without git: download the ZIP from the GitHub page (green **Code → Download ZIP** button), unzip it, and open the folder in the Terminal.*

**3. Launch Scribo** — this single command installs Python if needed, all dependencies, then starts the server:

```bash
uv run extracteur.py
```

Then open **http://localhost:8000/extractorultimator.html** in your browser.

> On the first extraction, the model (~4 GB) downloads once. After that, everything is local.

Drop a document — **PDF or image, Scribo adapts on its own** — click **Extract**, and copy the fields in one click. Nothing goes over the network: you can turn off the Wi-Fi and check.

---

## 🗺️ Planned evolution

A **double-clickable Mac application** (`.app`, no terminal) is being considered for general-public use — it requires an Apple packaging and signing step, reserved for a future release. In the meantime, `uv` offers the simplest path: one command, no Python prerequisite.

---

## 🎯 The product problem

Filling in a subscription form's fields by hand from a document (copying a 27-character IBAN, a BIC, an account holder's name) is slow and error-prone. Tools exist to automate this — but almost all of them **send the document to a remote server** to analyze it.

For an individual working on their own bank details, that doesn't matter. But as soon as an organization processes **someone else's** documents and must answer for them — healthcare, public sector, regulated professions — sending a sensitive document to a third-party cloud becomes a compliance problem, not a convenience one.

**Scribo's angle: what if the model came to the document, instead of the document going to the model?**

That's a product decision before it's a technical one. Choosing local processing isn't a tinkerer's taste: it's what makes a promise — "nothing leaves" — true *by construction* rather than *by contract*.

---

## 🏛️ The architecture

```
┌─────────────────────────── user's machine ────────────────────────────┐
│                                                                        │
│   document              local server (Python)             browser      │
│   ───────                ──────────────────                ───────      │
│   RIB.pdf   ──────────▶  1. reading  (pdfplumber)                       │
│                          2. extraction  (Mistral 7B / MLX)              │
│                          3. key checks  (mod-97…)  ──────▶  fields +    │
│                          4. temporary file erased           copy        │
│                                                                         │
│              no network egress — everything stays in this frame         │
└─────────────────────────────────────────────────────────────────────────┘
```

The model doesn't read the image directly: an OCR / text extractor (`pdfplumber`, or character recognition for a scan) provides the raw text, which Mistral then structures into JSON. This reading / interpretation split is what lets a 7B model do well: it doesn't "reason", it spots patterns in provided text.

---

## 🧮 The decision that matters most: verify, don't trust

A 7B model can make mistakes, or hallucinate a character. Scribo's answer is **not** to have the result re-read by a second model (two 7Bs share the same biases). It's deterministic:

- **IBAN** → validated by the **mod-97 key** (the ISO 7064 standard). Once the IBAN is validated, the bank code, branch code, account number and RIB key are **not read by the model**: they are **sliced from the IBAN**. Four fields that *cannot* be wrong.
- **BIC** → validated by its structure (ISO 9362 regex).
- **Per-field confidence score** → computed, not declared by the model: 50% base, +30 if the value appears verbatim in the source text, +20 if it passes its form check.

> The principle: **a value validated by computation cannot be a hallucination.** The LLM proposes, arithmetic disposes.

---

## 🗂️ Repository structure

| File | Role |
|---|---|
| `extracteur.py` | Local server: model loading (MLX), document reading, extraction, checks, `/extract` API. |
| `extractorultimator.html` | Interface: document drop, field display with scores, copy-paste. |
| `scribo.html` | Landing + playable demo (fictional data) — the project's showcase. |
| `docs/` | Banner and screenshots. |

---

## 🧭 Technical decisions

A few choices, and the *why* — this is where the product thinking shows:

- **MLX rather than llama.cpp** → native Apple Silicon inference, consistent with a "Mac workstation" target.
- **Temperature 0 at extraction** → we want no creativity, only fidelity to the document.
- **Capped generation (160 tokens)** → a RIB JSON is ~70 tokens; capping speeds things up without ever truncating.
- **Model preloaded at startup** → the (one-time) loading cost is moved out of the first document, it becomes invisible.
- **The document doesn't survive the request** → written to a temporary file, read, deleted in a `finally`.
- **Deterministic cleanup of ambiguous fields** → e.g. a RIB's "domiciliation" often mixes the branch and the account holder's address; a code rule isolates the branch, as a safety net behind the model's instruction.

---

## 🚧 Acknowledged limits

An honest prototype says what it doesn't do:

- **Deterministic cleanup** assumes the branch name precedes the address; a RIB in the reverse order would trip it up.
- **macOS Apple Silicon only** (MLX dependency). It's a choice, not an oversight: sovereign local processing only makes sense on a controlled machine.
- **No app signing or installer**: this repo runs from source. The `.app`/`.dmg` packaging is a later product step.

---

## 🗺️ Roadmap

- **Batch extraction (multi-document)** — drop several documents of different kinds (RIB, passports…) at once and extract the whole set in one go, with each file's type detected automatically. This is the next major planned evolution.
- **Customizable export (JSON / CSV)** — choose the output format (JSON or CSV) and select which fields to include, to plug Scribo directly into your own tools, spreadsheets or forms.
- New document types (vehicle registration, tax notice, proof of address — standardized formats first).
- Eventually, form auto-fill via a browser extension.

---

<p align="center">
  <sub>Demonstration project. Fictional sample data. Name and positioning subject to change.<br>
  No certification (HDS, SecNumCloud) claimed — the described value comes from the local processing architecture.</sub>
</p>

---

<a name="-français"></a>
# 🇫🇷 Français

<p align="center">
  <a href="#english">English</a> · <strong>Français</strong>
</p>

<p align="center">
  <img src="docs/banner.png" alt="Scribo — extraction souveraine de documents, Mistral 7B en local" width="100%">
</p>

<p align="center">
  <strong>Extraction de champs depuis des documents, sans qu'aucune donnée ne quitte la machine.</strong><br>
  Mistral 7B tourne en local via MLX · les valeurs sont vérifiées par le calcul, pas seulement générées.
</p>

<p align="center">
  <a href="#-lancer-en-local">Lancer en local</a> ·
  <a href="#-le-problème-produit">Le problème</a> ·
  <a href="#-larchitecture">Architecture</a> ·
  <a href="#-décisions-techniques">Décisions</a> ·
  <a href="#-limites-assumées">Limites</a>
</p>

---

## En une phrase

Scribo lit un document (un RIB, pour commencer), en extrait les champs utiles, **recontrôle chaque valeur par une règle de calcul**, et les rend prêts à coller dans un formulaire — le tout en tournant **entièrement sur la machine de l'utilisateur**, sans appel réseau.

C'est un prototype produit : il fonctionne de bout en bout, mais il est volontairement resté simple pour rester lisible. Ce README explique autant le *raisonnement produit* que le code.

---

## ⚡ Lancer en local

> ⚠️ **Plateforme : Mac Apple Silicon uniquement** (puce M1, M2, M3 ou plus récente).
> Scribo **ne fonctionne pas** sur Windows, Linux, ni sur Mac Intel, car son moteur d'inférence repose sur **MLX**, la bibliothèque d'Apple spécifique à ses puces. Une version portable (via llama.cpp) pourra être envisagée plus tard.

Scribo s'installe avec **[uv](https://docs.astral.sh/uv/)**, qui gère tout pour vous : il installe la bonne version de Python si elle manque, crée un environnement isolé et télécharge les dépendances — le tout automatiquement. **Pas besoin d'avoir Python au préalable.**

**1. Installez `uv`** (une seule fois, si vous ne l'avez pas déjà) :

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. Récupérez Scribo**, au choix :

```bash
# avec git
git clone https://github.com/Gabsuisse/scribo.git
cd scribo
```

*Ou sans git : téléchargez le ZIP depuis la page GitHub (bouton vert **Code → Download ZIP**), décompressez-le, et ouvrez le dossier dans le Terminal.*

**3. Lancez Scribo** — cette seule commande installe Python si besoin, toutes les dépendances, puis démarre le serveur :

```bash
uv run extracteur.py
```

Puis ouvrez **http://localhost:8000/extractorultimator.html** dans votre navigateur.

> À la première extraction, le modèle (~4 Go) se télécharge une fois. Ensuite, tout est local.

Déposez un document — **PDF ou image, Scribo s'adapte tout seul** — cliquez sur **Extraire**, et copiez les champs d'un clic. Rien ne part sur le réseau : vous pouvez couper le Wi-Fi et vérifier.

---

## 🗺️ Évolution envisagée

Une **application Mac double-cliquable** (`.app`, sans terminal) est à l'étude pour un usage grand public — elle demande une étape de packaging et de signature Apple, réservée à un futur lancement. En attendant, `uv` offre le parcours le plus simple : une commande, aucun prérequis Python.

---

## 🎯 Le problème produit

Remplir à la main les champs d'un formulaire de souscription à partir d'un document (recopier un IBAN de 27 caractères, un BIC, un titulaire) est lent et source d'erreurs. Des outils existent pour automatiser ça — mais presque tous **envoient le document vers un serveur distant** pour l'analyser.

Pour un particulier sur son propre RIB, ça n'a aucune importance. Mais dès qu'une organisation traite les documents **d'autrui** et doit en répondre — santé, secteur public, professions réglementées — envoyer une pièce sensible dans un cloud tiers devient un problème de conformité, pas de confort.

**L'angle de Scribo : et si le modèle venait au document, au lieu que le document parte vers le modèle ?**

C'est une décision produit avant d'être une décision technique. Le choix du traitement local n'est pas un goût de bricoleur : c'est ce qui rend une promesse — « rien ne sort » — vraie *par construction* plutôt que *par contrat*.

---

## 🏛️ L'architecture

```
┌─────────────────────── machine de l'utilisateur ───────────────────────┐
│                                                                         │
│   document              serveur local (Python)            navigateur    │
│   ───────                ──────────────────                ──────────    │
│   RIB.pdf   ──────────▶  1. lecture  (pdfplumber)                        │
│                          2. extraction  (Mistral 7B / MLX)               │
│                          3. contrôle des clés  (mod-97…)  ──▶  champs +   │
│                          4. fichier temporaire effacé          copier    │
│                                                                          │
│              aucune sortie réseau — tout reste dans ce cadre             │
└──────────────────────────────────────────────────────────────────────────┘
```

Le modèle ne lit pas l'image directement : un OCR/extracteur de texte (`pdfplumber`, ou reconnaissance de caractères pour un scan) fournit le texte brut, que Mistral structure ensuite en JSON. Cette séparation lecture / interprétation est ce qui permet à un modèle 7B de bien s'en sortir : il ne « raisonne » pas, il repère des motifs dans un texte fourni.

---

## 🧮 La décision qui compte le plus : vérifier, ne pas faire confiance

Un modèle 7B peut se tromper, ou halluciner un caractère. La réponse de Scribo n'est **pas** de faire relire le résultat par un second modèle (deux 7B partagent les mêmes biais). Elle est déterministe :

- **IBAN** → validé par la **clé mod-97** (la norme ISO 7064). Une fois l'IBAN validé, le code banque, le code guichet, le numéro de compte et la clé RIB ne sont **pas lus par le modèle** : ils sont **découpés depuis l'IBAN**. Quatre champs qui ne *peuvent pas* être faux.
- **BIC** → validé par sa structure (regex ISO 9362).
- **Score de confiance par champ** → calculé, pas déclaré par le modèle : 50 % de base, +30 si la valeur se retrouve telle quelle dans le texte source, +20 si elle passe son contrôle de forme.

> Le principe : **une valeur validée par le calcul ne peut pas être une hallucination.** Le LLM propose, l'arithmétique dispose.

---


## 🗂️ Structure du dépôt

| Fichier | Rôle |
|---|---|
| `extracteur.py` | Serveur local : chargement du modèle (MLX), lecture du document, extraction, contrôles, API `/extract`. |
| `extractorultimator.html` | Interface : dépôt du document, affichage des champs avec scores, copier-coller. |
| `scribo.html` | Landing + démo jouable (données fictives) — la vitrine du projet. |
| `desinstaller.sh` | Retire proprement le modèle en cache et les dépendances, avec confirmation à chaque étape. |
| `docs/` | Bannière et captures. |

---

## 🧹 Désinstaller

Scribo télécharge un modèle d'environ 4 Go dans `~/.cache/huggingface`. Pour tout nettoyer sans commande manuelle risquée, lancez le désinstallateur fourni :

```bash
bash desinstaller.sh
```

Il vous demande confirmation **avant chaque suppression** (modèle en cache, puis dépendances Python une par une) et ne touche à rien sans votre accord. Le dossier du projet lui-même se supprime ensuite à la main, depuis le Finder.

---

## 🧭 Décisions techniques

Quelques choix, et le *pourquoi* — c'est là que se lit la pensée produit :

- **MLX plutôt que llama.cpp** → inférence native Apple Silicon, cohérent avec une cible « poste de travail Mac ».
- **Température 0 à l'extraction** → on ne veut aucune créativité, seulement de la fidélité au document.
- **Génération plafonnée (160 tokens)** → un JSON de RIB fait ~70 tokens ; plafonner accélère sans jamais tronquer.
- **Préchargement du modèle au démarrage** → le coût de chargement (une fois) est déplacé hors du premier document, il devient invisible.
- **Le document ne survit pas à la requête** → écrit en fichier temporaire, lu, supprimé dans un `finally`.
- **Nettoyage déterministe des champs ambigus** → ex. la « domiciliation » d'un RIB mélange souvent l'agence et l'adresse du titulaire ; une règle en code isole l'agence, en filet de sécurité derrière la consigne au modèle.

---

## 🚧 Limites assumées

Un prototype honnête dit ce qu'il ne fait pas :

- **Un seul type de document** (RIB) pour l'instant. L'architecture est prête pour d'autres (chaque type = un schéma + ses contrôles), mais un seul est implémenté.
- **Le nettoyage de la domiciliation** suppose que le nom d'agence précède l'adresse ; un RIB à l'ordre inverse le mettrait en défaut.
- **macOS Apple Silicon uniquement** (dépendance MLX). C'est un choix, pas un oubli : le local souverain n'a de sens que sur une machine maîtrisée.
- **Pas de signature d'app ni d'installeur** : ce dépôt se lance depuis les sources. L'empaquetage `.app`/`.dmg` est une étape produit ultérieure.

---

## 🗺️ Suite envisagée

- **Extraction par lot (multi-documents)** — déposer plusieurs documents de natures différentes (RIB, passeports…) en une fois et lancer l'extraction de l'ensemble d'un coup, le type de chaque fichier étant détecté automatiquement. C'est la prochaine évolution majeure prévue.
- **Export personnalisable (JSON / CSV)** — choisir le format de sortie (JSON ou CSV) et sélectionner les champs à inclure, pour brancher directement Scribo sur ses propres outils, tableurs ou formulaires.
- Nouveaux types de documents (carte grise, avis d'imposition, justificatif de domicile — les formats standardisés d'abord).
- À terme, auto-remplissage de formulaire via extension navigateur.

---

<p align="center">
  <sub>Projet de démonstration. Données d'exemple fictives. Nom et positionnement susceptibles d'évoluer.<br>
  Aucune certification (HDS, SecNumCloud) revendiquée — la valeur décrite relève de l'architecture de traitement local.</sub>
</p>
