# Scribo : versionnage des lots

Date : 04/11/2026
Version de la règle : v1

## 1. Deux numéros distincts

- Le numéro de lot est séquentiel, écrit sur deux chiffres dans les noms de dossier (lot-07), jamais réutilisé, même si le lot est abandonné.
- La version produit suit semver (majeur.mineur.patch). Elle ne change que si le produit change.

Un lot qui ne change que la documentation ou le dispositif ne consomme pas de version produit. Il prend un numéro de lot et la mention "(doc seule)" dans l'historique.

## 2. Règle semver pour Scribo

| Niveau | Quand | Exemples |
|---|---|---|
| Patch (x.x.+1) | Correction de bug, ajustement visuel ou de texte, correction d'une règle de lint | Variable CSS manquante, rayon à corriger, libellé |
| Minor (x.+1.0) | Nouvelle fonctionnalité ou nouveau composant qui ne casse rien | Nouvelle famille de documents, export JSON ou CSV, extraction par lot, nouveau panneau |
| Major (+1.0.0) | Changement qui casse l'existant | Format de réponse de /extract modifié, méthode de lancement changée, version de Python minimale relevée, sens d'un niveau de fiabilité modifié |

Tant que le produit est en 0.x, un changement cassant incrémente le minor (convention semver de la série 0.x). Le passage à 1.0.0 est une décision de Gabriel, écrite dans decisions.md (voir D-003, décidé le 04/11/2026).

Quand le choix n'est pas évident, Claude propose une version et la justifie en une phrase dans le récap de clôture.

## 3. Cycle de vie d'un lot

| Statut | Signification | Qui le pose |
|---|---|---|
| Cadré | Le lot existe dans le carnet, pas encore validé | Claude |
| Validé | Récap validé par Gabriel, brief écrit | Claude |
| En code | L'agent Code travaille | Agent Code |
| En lint | Le lot est chez l'agent Lint, passage 1 ou 2 | Agent Lint |
| Refusé 1 | Premier refus, rapport renvoyé au Code | Agent Lint |
| Escalade | Deuxième refus, intervention de Gabriel demandée | Agent Lint |
| Suspendu | Escalade vers un nouveau workshop | Agent Lint |
| Validé lint | Lint passé, avec ou sans réserves | Agent Lint |
| Déposé | Branche poussée et PR ouverte | Agent Lint |
| Fusionné | PR fusionnée sur main par Gabriel, tag posé | Gabriel |
| Abandonné | Lot arrêté, numéro conservé | Gabriel |

Transitions normales : Cadré, Validé, En code, En lint, Validé lint, Déposé, Fusionné.
Avec refus : En lint, Refusé 1, En code, En lint, puis Validé lint ou Escalade. Escalade mène à une décision dans le Lint (retour En lint) ou à Suspendu (nouveau workshop).

## 4. Nommage

- Dossier du lot dans le dépôt : lots/lot-NN/ avec brief.md, passation.md, rapport-lint-1.md et, si besoin, rapport-lint-2.md.
- Branche : lot/NN-slug-court (exemple : lot/07-export-json).
- Commits : "Lot NN: titre court".
- Pull request : "Lot NN (vX.Y.Z): titre".
- Tag Git : vX.Y.Z, posé à la fusion sur main, jamais avant.

## 5. Version provisoire et version définitive

Le brief porte une version proposée. Elle est confirmée à la fusion. Si le lot est suspendu ou abandonné, la version n'est pas consommée et le lot suivant peut la reprendre.

## 6. Bloc méta et historique des docs

En tête de agent.md et design.md :

Date : JJ/MM/AAAA
Lot : n°X
Version produit : vX.Y.Z

En bas, une ligne d'historique par lot, sans réécrire le fichier :

- vX.Y.Z (Lot N, JJ/MM/AAAA) : description courte

La règle R08 du lint vérifie que le bloc méta, la version du brief, la ligne d'historique et le registre sont cohérents.

## 7. Registre et dérogations

- lots/REGISTRE.md est mis à jour à chaque changement de statut.
- Une décision prise dans le Lint qui assouplit une règle est écrite dans decisions.md avec un identifiant D-NNN et le lot concerné, puis reprise dans le brief du lot suivant.
