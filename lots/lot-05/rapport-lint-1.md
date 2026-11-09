# Rapport de lint

Date : 09/11/2026
Lot : n°05
Version produit : v0.7.1
Passage : 1
Verdict : Refusé (Refusé 1)

## Résumé

Constats bloquants : 2 (tous deux préexistants au lot, hors du périmètre du brief)
Avertissements : 2
Non vérifiables : 2
Script de lint : v1.0.0, `uv run --no-project lint/lint_scribo.py --root . --lot 05` : 0 bloquant, 3 avertissements, 4 points à relire. Règles passées : R01, R03 (13 tests), R04, R05, R07, R08, R09, R10, R11.

Les changements propres au lot sont conformes : lien Google Fonts supprimé, deux `@font-face` locaux (`extractorultimator.html:10-12`), `--filigrane` déclarée (`:21-22`), `pyproject.toml` et `uv.lock` en 0.7.1, IBAN de `design.md:176` remplacé par un spécimen (mod-97 recontrôlé = 1), log de `extracteur.py:583` sans nom de fichier, docs et registre à jour. Empreintes sha256 des trois fichiers de `fonts/` identiques à la passation, signature `wOF2` présente, `OFL.txt` avec la mention de copyright. Seules URL `https://` restantes dans l'app : deux liens `<a href>` (lignes 286 et 376), non chargés.

Le refus vient de la relecture du code existant, que le script signale "à relire" et qui n'a pas été modifié par le lot.

## Constats

| N° | Règle | Sévérité | Fichier et ligne ou test | Constat | Invariant | Correction suggérée |
|---|---|---|---|---|---|---|
| 1 | R02 | Bloquant | `extracteur.py:303` (RIB), `:509` (passeport) ; aucun fichier de test dans le dépôt | La logique relue est cohérente (IBAN affiché = IBAN contrôlé par mod-97 ; valeurs MRZ affichées = segments dont la clé est vérifiée), mais aucun test ne couvre "valeur affichée = valeur vérifiée" sur la sortie de `construire()` et `construire_passeport()`. Les 13 tests R03 testent les fonctions de calcul, pas les champs renvoyés. Préexistant. | Valeur affichée = valeur vérifiée (D-000c) | Ajouter des tests sur `construire()` et `construire_passeport()` : chaque champ au niveau `verifie` a une valeur égale à la valeur contrôlée (IBAN espacé, numéro sans `<`, dates ISO dérivées). Demande un cadre de test, donc une décision de périmètre (R04). |
| 2 | R07 | Bloquant | `extracteur.py:577-579` et `:89-91` | Le contenu du document est écrit (`f.write(donnees)`, `pix.save(...)`) avant le `try` dont le `finally` supprime le fichier. Si l'écriture échoue (disque plein, erreur PyMuPDF), le fichier temporaire, partiel mais contenant le document, reste sur le disque. Le script passe R07 car il voit bien un `finally`. Préexistant. | Fichiers temporaires supprimés sur tous les chemins | Ouvrir le `try` juste après la création du fichier, avant l'écriture, ou utiliser `mkstemp` avec suppression dans le `finally`. Deux lignes, mais le brief exclut toute modification de la gestion des fichiers temporaires. |
| 3 | R12 | Avertissement | `design.md:34` et `:254` | Les docs décrivent `--filigrane` comme le trait de "la guilloche du hero", mais l'app n'a aucun élément `#guilloche` (code mort CSS ligne 87, script lignes 467 à 479). L'écart est consigné dans la passation, pas dans `design.md`. | Cohérence docs/code | Mentionner dans `design.md` (section 4, dettes) que la guilloche est absente du DOM et que `--filigrane` est sans effet, en attendant la décision réintroduire / retirer. |
| 4 | R03 | Avertissement | Test script "limite connue" | Une date de naissance MRZ plus tard dans l'année courante est acceptée (2026-11-10) et peut s'afficher Vérifiée. Parquée par D-007, hors lot. | Vérification déterministe | Lot dédié prévu (D-007, `agent.md` section 6). |

Point délégué par le brief, R13 `extracteur.py:595` (`print(f"  Échec : {e}")`) : les exceptions levées par le code de Scribo ont des messages fixes (`:74`, `:112`, `:118`, `:183`, `:192`), et `json.loads` ne cite qu'une position. Je le tolère comme réserve, sans constat bloquant, mais les messages des bibliothèques tierces restent non vérifiables (voir ci-dessous).

## Non vérifiable

- R13, `extracteur.py:595` : le texte des exceptions de pdfplumber/pdfminer, PyMuPDF et mlx_lm ne peut pas être borné par relecture ; certaines erreurs de syntaxe PDF citent des jetons du fichier. Pour le fermer : afficher `type(e).__name__` au lieu de `e`.
- R01 à l'exécution réelle et rendu `.v-mono` / `.brut pre` avec des résultats : demandent `uv run extracteur.py` et le modèle MLX sur le Mac. Vérifié seulement sur page statique par l'agent Code (un seul hôte, deux graisses chargées).

## Réserves (si Validé avec réserves)

- Constats 3 et 4.
- R13 `extracteur.py:595`, voir plus haut.

## Faux positifs possibles

- R06 `lots/lot-05/brief.md:28` et `:56` : le brief cite l'ancien IBAN pour décrire le défaut ; ce n'est ni une démo ni un test. Faux positif (premier passage). Conséquence : le critère d'acceptation "plus d'avertissement R06" n'est pas atteint au sens strict, par le seul fait du brief. À signaler à Gabriel si cela se répète (exclure `lots/` de R06, ou ne plus citer d'IBAN invalide en clair dans les briefs).

## Décision demandée à Gabriel avant renvoi au Code

Les constats 1 et 2 sont préexistants et leur correction sort du brief (gestion des fichiers temporaires exclue, cadre de test à introduire). Les renvoyer tels quels au Code l'obligerait à sortir de son périmètre. Deux voies :

- A (recommandée) : dérogation D-008 pour le lot 5 seulement, constats 1 et 2 reportés dans le brief d'un lot dédié (lot 6), puisqu'elle touche R02. Le lot 5 repasse alors en Validé avec réserves sans nouvelle modification.
- B : révision 2 du brief du lot 5 pour inclure la correction R07 et les tests R02 ; le lot devient plus qu'un patch de conformité.

Décision de Gabriel (09/11/2026) : voie B, consignée en D-008. Le lot passe en Refusé 1. Le brief est révisé (révision 2) avant le retour à l'agent Code, qui reprend ensuite les constats 1 et 2, et de préférence les réserves 3 et R13 `:595` si la révision les inclut.

## Dépôt

Non déposé : verdict Refusé 1, et accord de Gabriel requis avant tout push ou PR. À noter pour le dépôt : les changements du lot ne sont pas encore commités (la branche `lot/05-conformite-lint` pointe sur le même commit que `main`, 687fdeb).
