# Scribo — Design system (design.md)

> Dernière mise à jour : 27/08/2026
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

- Vérifier le rendu réel du tag « valeurs divergentes / vérifié » dans les champs de
  la modale sur la vraie machine. **(à faire)**

*Résolu :* tag succès refondu en vert (`.tag-succes`, pendant du tag alerte) ;
rayons harmonisés (6px pour les CTA, 4px pour les tags).

---

## Historique

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
