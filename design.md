# Scribo — Design system (design.md)

Date : 29/08/2026
Lot : n°2
Version produit : v0.5.0

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

- **Le tampon de succès n'est pas le tag succès documenté.** Le bilan positif
  (« IBAN vérifié · mod-97 », « Clés MRZ vérifiées ») utilise toujours `.tampon`
  (cyan `#0C2E33` / `#8FE3F0`, radius 7px) alors que ce fichier documente
  `.tag-succes` (vert `#DEF8E5` / `#12B24A`, radius 4px) comme pendant du tag
  alerte. Les trois variantes coexistent dans le composant Figma `Tag` pour être
  comparées de visu. Trancher : soit `.tampon` devient le composant officiel du
  bilan global et `.tag-succes` reste au niveau champ, soit on migre.
  C'est aussi la seule occurrence de `border-radius:7px` restante dans l'app.
- **Les valeurs extraites ne sont pas en JetBrains Mono.** Le § 1 annonce
  JetBrains Mono pour les données extraites ; le code rend `.champ-val` en Clash
  Display avec `font-variant-numeric: tabular-nums`, et ne charge JetBrains Mono
  que pour `.brut pre`. Deux styles Figma existent — `Valeur/Champ` (le rendu
  réel) et `Valeur/Champ mono` (l'intention) — pour trancher en basculant le
  style sur les calques concernés.
- **La note de calcul parle d'IBAN sur l'écran passeport.** `m_note` est un texte
  i18n unique servi aux deux types de document ; il mentionne « clé mod-97 pour
  l'IBAN, format pour le BIC », deux champs absents d'un passeport. Corriger
  demande de scinder `m_note` en deux entrées × deux langues et de brancher la
  sélection sur le type de document.
- **Sept couleurs sont codées en dur hors du `:root`**, toutes de la famille
  feedback — celle qui bouge le plus :

  | Couleur | Où | Fichier |
  |---|---|---|
  | `#22C55E` | `.pastille.pret` | app |
  | `#FBBF24` | `.jauge.moyen` (texte et lueur des segments) | app, landing |
  | `#FF1F2E` | `.tag-alerte` (texte et icône) | app |
  | `#F8DEDE` | `.tag-alerte` (fond) | app |
  | `#0C2E33` | `.tampon` (fond) | app, landing |
  | `#8FE3F0` | `.tampon` (texte) | app, landing |
  | `#2C2C2C` | navbar mobile | landing |

- **`.tag-succes` n'existe pas dans le code.** Le § 2 le documente et
  l'historique v0.2.0 le donne pour résolu, mais ni la classe ni ses couleurs
  (`#DEF8E5`, `#12B24A`) n'apparaissent dans `extractorultimator.html` ou
  `scribo.html`. Le composant a été spécifié puis jamais écrit. C'est la même
  dette que `.tampon`, vue de l'autre côté : il n'y a pas deux composants à
  départager, il y en a un qui existe et un qui n'a jamais été implémenté.
- **`#FB6E57` est documenté au § 1 mais absent des deux fichiers.** Soit le CTA
  clair de la navbar a été retiré, soit la valeur a changé. À vérifier avant de
  la garder dans les tokens.
- **Les espacements n'ont pas d'échelle.** 22 valeurs distinctes relevées dans le
  CSS, dont 9-10-11-12 et 20-21-22 qui coexistent. La planche Fondations du
  fichier Figma les affiche en barres, l'écart se voit d'un coup d'œil.
- Vérifier le rendu réel du tag « valeurs divergentes / vérifié » dans les champs
  de la modale sur la vraie machine. **(à faire)**

### Résolues

- **`var(--encre)`** (lot 2) : la variable n'était déclarée nulle part, la
  propriété était donc invalide et la couleur retombait en héritage — le rendu
  était correct par accident. Remplacée par `var(--d-txt)` sur le CTA
  « Extraire un autre RIB ».
- **Harmonisation des rayons à 6px** (lot 2) : annoncée au lot v0.2.0, appliquée
  seulement maintenant sur `.cta`, `.tout-copier`, `.dl-json` et `.lang-trigger`.
  `.tampon` reste à 7px tant que son sort n'est pas tranché. La landing
  (`scribo.html`) conserve deux `border-radius:7px` sur `.lang-trigger` et
  `.controles-copie`, hors périmètre de ce lot.
- Tag succès refondu en vert (`.tag-succes`, pendant du tag alerte) ; rayons des
  tags harmonisés à 4px.

## Historique

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
