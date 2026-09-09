# Scribo — Passation lot 2 vers la conversation code

Date : 29/08/2026 · Version produit : v0.5.0 · Fichier concerné : `scribo_repo_v0.2/`

Ce document résume un lot de travail design mené en dehors de la conversation code.
Il contient ce qui a été **modifié dans le code**, ce qui a été **volontairement
laissé en l'état**, et les **dettes ouvertes** avec assez de détail pour être
traitées sans contexte supplémentaire.

---

## 1. Modifications appliquées au code

Un seul fichier touché : `extractorultimator.html`. Cinq lignes. Aucun changement
fonctionnel, contrôle de parsing JS passé.

### 1.1 Bug — variable CSS inexistante

`--encre` n'est déclarée nulle part, ni dans `extractorultimator.html` ni dans
`scribo.html` (vérifié : zéro occurrence de `--encre:`). La propriété était donc
invalide au calcul, et la couleur retombait en héritage depuis `.modale-corps`,
c'est-à-dire `--d-txt`. Le rendu était correct par accident.

```diff
  <!-- CTA « Extraire un autre RIB » du bloc résultats -->
- <button class="cta" id="btnRecommencer" style="background:transparent;color:var(--encre);border:1px solid var(--trait)"
+ <button class="cta" id="btnRecommencer" style="background:transparent;color:var(--d-txt);border:1px solid var(--trait)"
```

### 1.2 Harmonisation des rayons à 6px

Annoncée dans l'historique de `design.md` au lot v0.2.0 (« CTA 7px → 6px »),
jamais appliquée dans le code. Quatre sélecteurs corrigés :

| Sélecteur | Avant | Après |
|---|---|---|
| `.lang-trigger` | `border-radius:7px` | `border-radius:6px` |
| `.tout-copier` | `border-radius:7px` | `border-radius:6px` |
| `.dl-json` | `border-radius:7px` | `border-radius:6px` |
| `.cta` | `border-radius:7px` | `border-radius:6px` |

---

## 2. Volontairement non modifié

- **`.tampon` reste à `border-radius:7px`.** C'est désormais la seule occurrence
  de 7px dans l'app. Ce n'est pas un CTA, et son sort dépend de la dette 3.1
  ci-dessous — le changer maintenant reviendrait à préjuger de la décision.
- **`scribo.html` (landing) n'a pas été touchée.** Elle conserve deux
  `border-radius:7px`, sur `.lang-trigger` et `.controles-copie`. Le lot portait
  sur l'app uniquement.

---

## 3. Dettes ouvertes

### 3.1 `.tag-succes` est spécifié mais n'existe pas dans le code

`design.md` § 2 documente un `.tag-succes` vert (`#DEF8E5` / `#12B24A`,
radius 4px) comme pendant du `.tag-alerte`, et son historique v0.2.0 le donne
pour **résolu**. Vérification faite : ni la classe ni ses deux couleurs
n'apparaissent dans `extractorultimator.html` ni dans `scribo.html`.

Le bilan positif est rendu par `.tampon` (cyan `#0C2E33` / `#8FE3F0`, radius 7px,
SemiBold 12 majuscules), qui ne ressemble pas au tag alerte.

Il n'y a donc pas deux composants à départager mais un composant existant et une
spécification jamais écrite. Deux issues :

- soit `.tampon` devient officiellement le composant du bilan global, et
  `design.md` doit être corrigé pour cesser d'annoncer `.tag-succes` comme
  résolu ;
- soit `.tag-succes` est implémenté et `.tampon` migre vers lui.

### 3.2 Les valeurs extraites ne sont pas en JetBrains Mono

`design.md` § 1 annonce JetBrains Mono pour les données extraites. Le code rend
`.champ-val` en Clash Display avec `font-variant-numeric: tabular-nums`, et ne
charge JetBrains Mono que pour `.brut pre`.

Soit on corrige la doc, soit on ajoute `font-family:"JetBrains Mono",monospace`
sur `.champ-val .v-mono`.

### 3.3 La note de calcul parle d'IBAN sur l'écran passeport

`m_note` est un texte i18n **unique**, servi aux deux types de document. Il
mentionne « clé mod-97 pour l'IBAN, format pour le BIC » — deux champs absents
d'un passeport.

Emplacements :
- rendu : `<p class="note" data-i18n="m_note">` (~ligne 299)
- dictionnaires : `I18N.fr.m_note` (~ligne 342), `I18N.en.m_note` (~ligne 367)

Correction : scinder en `m_note_rib` / `m_note_passeport` dans les deux
dictionnaires, puis sélectionner selon `res.type` au moment du rendu des
résultats. C'est une petite fonctionnalité, pas un fix de style — d'où son report.

### 3.4 Sept couleurs codées en dur hors du `:root`

Toutes de la famille feedback, celle qui bouge le plus.

| Couleur | Sélecteur | Fichier |
|---|---|---|
| `#22C55E` | `.pastille.pret` | app |
| `#FBBF24` | `.jauge.moyen` (texte + lueur des segments) | app, landing |
| `#FF1F2E` | `.tag-alerte` (texte et icône) | app |
| `#F8DEDE` | `.tag-alerte` (fond) | app |
| `#0C2E33` | `.tampon` (fond) | app, landing |
| `#8FE3F0` | `.tampon` (texte) | app, landing |
| `#2C2C2C` | navbar mobile | landing |

Les remonter dans le `:root` sous des noms de feedback rendrait un futur
changement de palette trivial.

### 3.5 `#FB6E57` est documenté mais absent

`design.md` § 1 le donne comme « CTA orange plus clair (navbar landing, hover CTA
flottant) ». La valeur n'apparaît dans aucun des deux fichiers. Soit le CTA a été
retiré, soit la valeur a changé — à vérifier avant de la conserver comme token.

### 3.6 Les espacements n'ont pas d'échelle

22 valeurs distinctes relevées dans le CSS de l'app, dont `9-10-11-12` et
`20-21-22` qui coexistent. Ce n'est pas bloquant, mais c'est le chantier le plus
rentable des six : une échelle réduirait la surface de décision à chaque nouveau
composant.

---

## 4. Référence design

Le design system existe maintenant comme fichier Figma, construit à partir du CSS
de `extractorultimator.html` sans arrondir aucune valeur.

**Fichier** : « Scribo — Userflow » (équipe GD/HC).
**Pages** : Cover · Démarrer · Fondations · Atomes · Composés · Userflow.

**Variables** — 4 collections, 82 variables :

| Collection | Contenu |
|---|---|
| Primitives | 28 couleurs, `var(--…)` sur les 18 déclarées dans le `:root` |
| Couleur | 24 sémantiques aliasées : surface / texte / bordure / accent / feedback |
| Espacement | 22 valeurs nommées par leur valeur (voir 3.6) |
| Rayon | 8 : tag 4, petit 5, cta 6, tampon 7, carte 8, zone 10, modale 16, pill 999 |

**Typographie** — 37 styles, tous liés à la variable `typo/famille-ui`. Les
valeurs extraites sont liées à `typo/famille-donnees`.

**Composants** — 9, aucune valeur en dur : Bouton (5 variantes), Tag (3),
Statut serveur (3), Jauge de confiance (3 + 4 propriétés de segment),
Carte document (2), Ligne de champ (3), Zone de dépôt (4), Bloc erreur,
Barre de navigation.

**Écrans** — 11 artboards du userflow en 4 sections : Accueil, Extraction RIB,
Extraction Passeport, États limites.

**Styles isolés dans Figma que le CSS ne distinguait pas** — utiles si vous
refactorisez le CSS :

- `.fermer` est en **Medium 12px, ls .05em**, pas en SemiBold 14px comme les
  autres CTA. C'est une règle à part entière, pas une variante de `.cta`.
- `.fam-tete span` (« 1/4 disponible ») : Regular 12px.
- `.brut summary` : Medium 12px majuscules, ls .05em.

---

## 5. État des versions

`agent.md` et `design.md` sont à jour en **v0.5.0 (lot 2)**. La section 4 de
`design.md` est réorganisée en dettes **ouvertes** et **résolues** ; les six
dettes ci-dessus y figurent avec le même niveau de détail.
