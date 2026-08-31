# Scribo — Design system (design.md)

Date : 29/08/2026
Lot : n°3
Version produit : v0.6.0

---

> Documentation des choix UI/UX de Scribo (landing page + interface de l'app).
> Esthétique : éditoriale, contrastée, typographie forte.

---

## 1. Design tokens

### Typographie
- **Titres / UI** : **Clash Display** (variable). Graisses utilisées : 300 (light),
  400 (regular), 500 (medium), 600 (semibold), 700 (bold).
- **Données extraites / valeurs techniques** : **JetBrains Mono**.

### Couleurs — clair
| Token | Valeur | Usage |
|---|---|---|
| `--corail` | `#FF5A3C` | Accent principal, CTA |
| `--corail-fonce` | `#E8482B` | Hover du corail |
| `--bleu` | `#0AADCB` | Accent secondaire, eyebrows |
| `--bleu-dark` | `#3CC9E3` | Bleu en mode sombre |
| `--noir` | `#0E0E0F` | Texte fort, fonds sombres |
| `--blanc` | `#F4F3EF` | Fond clair (blanc cassé) |
| `--texte` | `#1A1A1C` | Texte courant |
| `--texte-2` | `#55555A` | Texte secondaire |
| `--trait` | `#DCDAD2` | Bordures, séparateurs |

CTA orange plus clair (navbar landing, hover CTA flottant) : **#FB6E57**.

### Couleurs — surfaces sombres (démo, interface app)
| Token | Valeur |
|---|---|
| `--d-surface` | `#09090B` |
| `--d-carte` | `#161618` |
| `--d-hover` | `#242427` |
| `--d-bord` | `#323236` |
| `--d-bord-fort` | `#3F3F46` |
| `--d-txt` | `#FAFAFA` |
| `--d-txt-2` | `#A1A1AA` |
| `--d-txt-3` | `#71717A` |

Navbar mobile (landing) et pill dark : fond gris **#2C2C2C**.

### Rayons
- Boutons / CTA : **6px**.
- Tag alerte / tag succès : **4px**.
- Pills / navbar : 999px (pleinement arrondi).

---

## 2. Composants clés

### — Communs (landing + app) —

#### Logo
- « S » stylisé, viewBox 181×161. **Noir sur fond transparent** (l'ancien fond
  orange a été retiré partout — landing et interface). En mode sombre, forcé en
  blanc (#FAFAFA) pour rester visible.

#### Tag alerte (status alerte du design system)
Style unifié, **réutilisable pour tous les tags d'alerte** du projet :
- Fond **#F8DEDE**, texte et icône **#FF1F2E**.
- Border-radius **4px**, **aucune bordure**.
- Typo **14px**, graisse **medium (500)**, casse normale (première lettre majuscule,
  pas de tout-majuscules).
- Icône **triangle d'alerte** (⚠).
- Classe CSS : `.tag-alerte`.

#### Tag succès (validation)
Pendant vert du tag alerte, **même style visuel** :
- Fond **#DEF8E5**, texte et icône **#12B24A** (vert vif).
- Border-radius **4px**, **aucune bordure**.
- Typo **14px**, graisse **medium (500)**, casse normale.
- Icône **coche** (✓).
- Classe CSS : `.tag-succes`.

Les deux tags (`.tag-alerte` rouge, `.tag-succes` vert) forment un couple cohérent
pour les status négatif / positif du design system.

### — Landing page —

#### Navbar
- **Desktop** : pill flottante en bas-centre, fond sombre, glisseur blanc piloté
  en JS (classe `.sous-glisseur`) — évite le `:has()` CSS fragile. Le logo flottant
  (haut-gauche) et un CTA « Try the project on GitHub » (haut-droite, pendant du logo)
  disparaissent au scroll. CTA en #FB6E57, hover orange.
- **Mobile** (`< 760px`) : la pill et le CTA flottant sont masqués ; navbar en haut
  avec logo + **burger** (fond #2C2C2C en dark, icône blanche). Le burger ouvre un
  **menu plein écran** qui s'adapte au thème (fond clair en clair, noir en sombre).
  Le sélecteur de langue y affiche l'état « selected ».

#### Section technique
- Deux colonnes : eyebrow + titre « The model proposes, arithmetic disposes » à
  gauche, explication à droite. (L'ancien bloc de code Python a été retiré, peu lisible.)

#### Marquee
- Frise défilante bilingue.

### — App locale (interface) —

#### Statut serveur (pill, 3 états)
- **Prêt** : pastille **verte** (#22C55E) + « Scribo prêt / Scribo ready ».
- **Chargement** : **loader animé** (spinner) + « Chargement du modèle… ». Polling
  toutes les 2 s → bascule auto vers « prêt » quand le modèle est chargé.
- **Injoignable** : pastille **rouge** + lien « En savoir plus » → modale d'aide
  (message court + lien vers le README GitHub).

#### Modale d'extraction
- **Header dynamique** selon le document choisi (titre + « ce que le système va lire »).
  RIB et passeport ont chacun leur texte. Re-traduit au changement de langue.
- **Zone fichier** : titre + sous-titre resserrés (gap 1px, line-height 1.2).
- **CTA central** en fin de zone : « Extract another document » (relance une sélection).
- **Barre d'actions** : « Copy all (name: value) » + « Download the JSON » côte à côte,
  12px d'écart, même hauteur que les CTA standard (47px).

#### Cards de documents (catalogue)
- Cards actives = cliquables (RIB, passeport). Cards inactives = grisées
  (opacity ~.45, curseur `not-allowed`) avec mention « Bientôt / Soon » — communique
  la vision produit sans surpromettre.

---

## 2 bis. Userflow et nomenclature des artboards

Le parcours de l'app est maquetté dans un canvas Claude Design (11 artboards,
écrans desktop 1440 px). Il sert de référence visuelle : chaque artboard est un
état réel de l'interface, repris des valeurs de `extractorultimator.html`.

**Nomenclature des artboards** (à respecter pour toute nouvelle maquette) :

```
NNx - Nom de section - Type et Nom de page (Status)
```

- `NN` = numéro de section (01, 02, 03…), `x` = lettre d'ordre dans la section.
- `Type` = `Écran` (page pleine) ou `Modale`.
- `Status` entre parenthèses = l'état précis représenté.

Les artboards d'une même section sont alignés **de gauche à droite**, une rangée
par section, et une note collante en tête de rangée porte l'intention.

**Sections et états couverts :**

| Section | Artboards |
|---|---|
| 01 — Accueil | Catalogue (Modèle en chargement), Catalogue (Prêt) |
| 02 — Extraction RIB | Dépôt (Vide), Dépôt (Fichier prêt), Extraction (Scan en cours), Résultats (IBAN vérifié) |
| 03 — Extraction Passeport | Dépôt (Vide), Résultats (Clés MRZ vérifiées) |
| 04 — États limites | Dépôt (Format refusé), Résultats (Clé MRZ invalide), Aide (Serveur injoignable) |

**Données de démo du canvas** — strictement fictives et arithmétiquement
cohérentes : IBAN `FR76 3000 4008 2800 0123 4567 890` (clé mod-97 valide,
décomposé en 30004 / 00828 / 00012345678 / 90), passeport SPECIMEN / MARIE
CLAIRE, FRA.

---

## 2 ter. Bibliothèque Figma

Le design system existe désormais comme fichier Figma, source partagée entre
designers. Il a été construit à partir du CSS de `extractorultimator.html`, sans
arrondir aucune valeur.

**Fichier** : « Scribo — Userflow », équipe GD/HC.

**Structure** : Cover · Démarrer · Fondations · Atomes · Composés · Userflow.

**Variables** (4 collections, 82 variables) :

| Collection | Contenu |
|---|---|
| Primitives | 28 couleurs, scopes vides, `var(--…)` sur les 18 déclarées dans le `:root` |
| Couleur | 24 sémantiques aliasées — surface / texte / bordure / accent / feedback, un seul mode |
| Espacement | 22 valeurs, nommées par leur valeur (aucune échelle ne les gouverne) |
| Rayon | 8 — tag 4, petit 5, cta 6, tampon 7, carte 8, zone 10, modale 16, pill 999 |

**Typographie** : 37 styles de texte, tous liés à la variable `typo/famille-ui`.
Changer cette seule valeur bascule le fichier entier d'une police à l'autre —
c'est le mécanisme qui permet de travailler sans Clash Display installée, puis de
la rétablir en un geste. Les valeurs extraites sont liées à `typo/famille-donnees`.

**Composants** (9, tous liés aux variables, aucune valeur en dur) :
Bouton (5 variantes), Tag (3), Statut serveur (3), Jauge de confiance (3 + 4
propriétés de segment), Carte document (2), Ligne de champ (3), Zone de dépôt (4),
Bloc erreur, Barre de navigation.

**Styles ajoutés que le CSS n'isolait pas** : `CTA/Fermer` (`.fermer` est en
Medium 12px, pas en SemiBold 14px comme les autres CTA), `Étiquette/Disponibilité`
(`.fam-tete span`), `Brut/Résumé` (`.brut summary`), et le token `rayon/tampon`
à 7px.

**Écrans** : les 11 artboards du userflow, regroupés en 4 sections Figma
correspondant aux sections de la nomenclature (§ 2 bis).

---

## 3. Principes UX / layout

- **Bilingue FR/EN** partout (landing + app), via dictionnaires i18n + `data-i18n`.
- **Dark/light mode** avec persistance (localStorage) sur la landing.
- **Minimalisme éditorial** : grands titres Clash Display, beaucoup de blanc,
  hiérarchie forte, accents corail/bleu parcimonieux.
- **Honnêteté du statut** : l'UI reflète l'état réel (serveur, fiabilité des champs).
  Un champ non garanti affiche un score plus bas et/ou un tag — jamais un faux
  « vérifié ».

---

## 4. Dettes / incohérences de design identifiées

### Ouvertes

- **`#FB6E57` (CTA orange clair de la navbar landing).** Documenté au § 1, mais
  absent de `extractorultimator.html` et de `scribo.html`. Décision : la valeur est
  conservée dans les tokens (usage landing : hover du CTA flottant / navbar). À
  vérifier / réappliquer côté `scribo.html` lors d'un prochain lot landing.
- **Les espacements du CSS ne sont pas encore tous rattachés à l'échelle.** Une
  échelle `--space-1..12` (4/8/12/16/20/24/32/40/48) a été introduite dans le `:root`
  de l'app comme référence, mais les ~22 valeurs existantes n'ont pas été migrées
  dessus (trop risqué visuellement en une passe). À migrer composant par composant.
- Vérifier le rendu réel du tag « valeurs divergentes / vérifié » et du tag succès
  vert dans la modale sur la vraie machine. **(à faire)**

### Résolues

- **`.tag-succes` implémenté** (lot 3) : le bilan positif (« IBAN vérifié · mod-97 »,
  « Clés MRZ vérifiées ») utilise désormais `.tag-succes` (vert `#DEF8E5` / `#12B24A`,
  radius 4px, medium, icône coche), pendant exact du `.tag-alerte`. L'ancien `.tampon`
  cyan est supprimé — ce qui élimine la dernière occurrence de `border-radius:7px`
  dans l'app.
- **Valeurs extraites en JetBrains Mono** (lot 3) : `.champ-val .v-mono` charge
  désormais `"JetBrains Mono", monospace` (16px, tabular-nums), conforme au § 1.
- **Note de calcul scindée par type** (lot 3) : `m_note` unique remplacé par
  `m_note_rib` / `m_note_passeport` (× 2 langues), sélectionné selon `res.type`. La
  note passeport parle de la MRZ (ICAO 9303), plus de l'IBAN/BIC.
- **Couleurs feedback remontées dans le `:root`** (lot 3) : `--ok` (#22C55E),
  `--moyen` (#FBBF24), `--alerte-txt`/`--alerte-bg`, `--succes-txt`/`--succes-bg`,
  `--gris-nav` (#2C2C2C). Plus aucune couleur feedback en dur dans l'app.
- **`var(--encre)`** (lot 2) : remplacée par `var(--d-txt)` sur le CTA
  « Extraire un autre RIB ».
- **Harmonisation des rayons à 6px** (lot 2) : `.cta`, `.tout-copier`, `.dl-json`,
  `.lang-trigger`. La landing (`scribo.html`) conserve deux `border-radius:7px`
  hors périmètre.

## Historique

- v0.6.0 (Lot 3, 29/08/2026) : résolution dans le code de cinq dettes consignées au
  lot 2 — `.tag-succes` implémenté (et `.tampon` supprimé), valeurs en JetBrains Mono,
  `m_note` scindée RIB/passeport, couleurs feedback remontées dans le `:root`, échelle
  d'espacement `--space-*` introduite comme référence. Section 4 mise à jour.
- v0.5.0 (Lot 2, 29/08/2026) : construction de la bibliothèque Figma (§ 2 ter) —
  82 variables, 37 styles de texte, 9 composants, 11 écrans. Trois divergences
  supplémentaires consignées (JetBrains Mono, `m_note` générique, couleurs hors
  `:root`) et deux résolues dans le code (`var(--encre)`, rayons à 6px).
  Réorganisation de la section 4 en dettes ouvertes / résolues.
- v0.4.0 (Lot 1, 29/08/2026) : ajout de la section « Userflow et nomenclature
  des artboards » (canvas 11 écrans) ; ajout de deux dettes de design identifiées
  en relisant la source (`var(--encre)` non déclarée, `.tampon` vs `.tag-succes`) ;
  ajout du bloc méta en tête de fichier.
- v0.3.0 (27/08/2026) : restructuration des composants en trois groupes — Communs
  (logo, tags), Landing (navbar, section technique, marquee), App locale (statut
  serveur, modale, cards).
- v0.2.0 (27/08/2026) : ajout du tag succès vert (`.tag-succes`, pendant du tag
  alerte) ; harmonisation des rayons (CTA 7px → 6px, tags 4px).
- v0.1.1 (27/08/2026) : retrait des références à l'inspiration externe (section
  « Références visuelles » supprimée).
- v0.1.0 (27/08/2026) : création. Documente les tokens (couleurs, typo Clash Display +
  JetBrains Mono), la navbar landing (desktop pill + mobile burger/menu plein écran),
  les 3 états du statut serveur, la modale d'extraction à header dynamique, et le
  **tag alerte** (#FF1F2E / #F8DEDE, radius 4px, medium, icône triangle).
