# Dossier de lot

Date : 04/11/2026
Lot : n°05
Version produit proposée : v0.7.1
Justification de la version : correctifs de conformité sans nouvelle fonctionnalité ni changement de comportement d'extraction, donc un patch.
Statut : Validé
Révision du brief : 1

## Titre

Conformité lint : polices en local, variable filigrane, version, IBAN d'exemple, log

## Origine

Workshop n°1 du 04/11/2026. Premier passage du script de lint sur le code réel : il remonte un écart bloquant (R01) et plusieurs écarts mineurs (R09, R08, R06, R13). Aucun lot suspendu, aucune escalade.

## Objectif

Mettre le code existant en conformité avec les règles du lint, sans changer le comportement de l'extraction ni de la vérification.

## Périmètre

Inclus :
- Polices en local (R01) : supprimer le lien Google Fonts de `extractorultimator.html` (ligne 4) et servir JetBrains Mono depuis le disque, graisses 400 et 500, avec son fichier de licence OFL.
- Variable `--filigrane` (R09) : la déclarer dans le `:root` de `extractorultimator.html`.
- Version (R08) : passer `version` de `pyproject.toml` de "0.1.0" à "0.7.1".
- IBAN d'exemple (R06) : remplacer, dans `design.md` (ligne 174), l'IBAN `FR76 3000 4008 2800 0123 4567 890` (clé mod-97 invalide) par un IBAN de `lint/specimens.json`.
- Log (R13) : retirer le nom du fichier du message console de `extracteur.py` (ligne 583).
- Mises à jour de `agent.md` et `design.md` (voir plus bas), version v0.7.1.

Exclus :
- Règle du siècle sur la date de naissance MRZ (point parké, lot ultérieur, voir D-007).
- Message d'exception affiché à `extracteur.py:595` (non discuté au workshop, voir Risques).
- Toute modification du script de lint, de ses règles ou de `lint/specimens.json`.
- La landing `scribo.html` et le canvas Figma.
- Toute nouvelle fonctionnalité et toute modification de la logique de vérification ou des niveaux Vérifié / Probable / À vérifier.

## Décisions applicables

- D-000a : tout est embarqué en local, zéro appel réseau.
- D-000e : front vanilla en fichier unique, pas de chaîne de build, pas de Tailwind.
- D-005 : le script de lint et la liste des spécimens vivent dans le dépôt (`lint/`).
- D-006 : JetBrains Mono est livrée avec l'app, licence OFL jointe.
- D-007 : la règle du siècle MRZ est parquée, hors de ce lot.

## Critères d'acceptation

Chaque critère est vérifiable sans interprétation.

- [ ] `extractorultimator.html` ne contient plus ni `fonts.googleapis.com` ni `fonts.gstatic.com`, ni aucune autre URL `http://` ou `https://` chargée au démarrage de la page.
- [ ] Une police JetBrains Mono (graisses 400 et 500) est servie depuis le dossier du dépôt, et les valeurs extraites (`.v-mono`) et le bloc brut (`.brut pre`) s'affichent avec elle.
- [ ] Le fichier de licence OFL de JetBrains Mono (avec la mention de copyright) est présent à côté des fichiers de police.
- [ ] `--filigrane` est déclarée dans le `:root`, avec une valeur tirée de la palette existante (pas de nouvelle couleur hors palette).
- [ ] `pyproject.toml` indique `version = "0.7.1"`.
- [ ] `design.md` ne contient plus l'IBAN `FR76 3000 4008 2800 0123 4567 890` ; l'IBAN qui le remplace figure dans `lint/specimens.json` et la phrase qui le décrit est cohérente avec lui (la décomposition banque / guichet / compte / clé de l'ancien IBAN est retirée ou réécrite).
- [ ] Le message console de `extracteur.py` à la ligne 583 n'inclut plus le nom du fichier, et indique toujours le nombre de caractères lus.
- [ ] `python3 lint/lint_scribo.py --root . --lot 05` ne remonte plus de constat sur R01, R08 et R09, plus d'avertissement R06, et aucun constat bloquant.
- [ ] Les 13 tests R03 du script de lint passent toujours.
- [ ] `agent.md` et `design.md` portent le bloc méta Date 04/11/2026, Lot n°05, Version produit v0.7.1, et une ligne d'historique v0.7.1.
- [ ] `lots/REGISTRE.md` passe le lot 5 à En code puis En lint au fil du travail.

## Invariants touchés

| Invariant | Touché | Précaution |
|---|---|---|
| Zéro réseau (R01) | oui | Le téléchargement des fichiers de police se fait une seule fois, à l'écriture du lot, hors de l'app. À l'exécution, la page ne fait aucune requête externe. |
| Valeur affichée = valeur vérifiée (R02) | non | Ne pas toucher aux fonctions qui attribuent les niveaux de fiabilité. |
| Vérification déterministe (R03) | non | Aucune modification de `iban_valide`, `mrz_cle` et consorts. |
| Pas de build ni Tailwind (R05) | oui | Les polices sont des fichiers statiques. Aucun outil de build, aucun paquet npm. |
| Données de démo fictives (R06) | oui | L'IBAN de remplacement vient de la liste des spécimens (confirmés fictifs par Gabriel le 04/11/2026). |
| Fichiers temporaires et logs (R07, R13) | oui | Le nom du fichier n'est plus écrit dans la console. La gestion des fichiers temporaires ne change pas. |

## Fichiers concernés

- `extractorultimator.html` : suppression du lien Google Fonts (ligne 4), ajout de `@font-face` pour JetBrains Mono, déclaration de `--filigrane` dans `:root`.
- `fonts/` (nouveau dossier) : fichiers de police JetBrains Mono 400 et 500 au format woff2, et `OFL.txt`.
- `pyproject.toml` : version.
- `extracteur.py` : ligne 583, message console.
- `design.md` : IBAN d'exemple, typographie, dettes, bloc méta, historique.
- `agent.md` : structure des fichiers, décisions techniques, ce qui reste à faire, bloc méta, historique.
- `lots/REGISTRE.md` : statuts du lot.

Choix de mise en œuvre pour les polices (non discuté au workshop) : le brief retient un dossier `fonts/` de fichiers woff2, servi par le serveur local comme le dossier `pdfjs/`. Le serveur hérite de `SimpleHTTPRequestHandler`, donc il sert déjà les fichiers statiques du dépôt. Alternative acceptable : intégrer la police en base64 dans le HTML, comme Clash Display. Si l'agent Code préfère cette voie, il le justifie dans la passation et adapte la mise à jour de `agent.md` (structure des fichiers).

## Mises à jour de documentation prêtes à appliquer

agent.md :
- Bloc méta : Date 04/11/2026, Lot n°05, Version produit v0.7.1.
- Section 2, Structure des fichiers : ajouter `fonts/` (JetBrains Mono woff2 et licence OFL, servis en local) et `lint/` (script de lint et liste des spécimens, hors exécution de l'app).
- Section 4, Décisions techniques : ajouter « Polices embarquées en local (lot 5) : JetBrains Mono est servie depuis `fonts/` au lieu de Google Fonts, pour tenir la promesse zéro réseau. Licence OFL jointe. »
- Section 5, Points d'attention : ajouter « Limite connue de la règle du siècle MRZ : une date de naissance postérieure à aujourd'hui, dans l'année en cours, est acceptée, car la règle compare seulement les années. Parkée pour un lot ultérieur (D-007). »
- Section 6, Ce qui reste à faire : ajouter « Traiter la règle du siècle MRZ (lot dédié, avec tests). » et « Décider du sort des deux IBAN de la landing (25 caractères, valides en mod-97 mais pas au format français de 27 caractères). »
- Historique : - v0.7.1 (Lot 5, 04/11/2026) : conformité lint. Police JetBrains Mono embarquée en local, `--filigrane` déclarée, version de `pyproject.toml` alignée, IBAN d'exemple de `design.md` corrigé, nom de fichier retiré du log console. Aucun changement fonctionnel.

design.md :
- Bloc méta : Date 04/11/2026, Lot n°05, Version produit v0.7.1.
- Section 1, Typographie : « Données extraites / valeurs techniques : JetBrains Mono, embarquée en local (graisses 400 et 500, dossier `fonts/`, licence OFL). »
- Section 1, Couleurs : documenter `--filigrane` et sa valeur choisie.
- Section 2 bis, Données de démo du canvas : remplacer l'IBAN invalide par l'IBAN retenu et ajuster la phrase. Le canvas Figma n'est pas modifié par ce lot.
- Section 4, Résolues : ajouter les trois points « Google Fonts remplacé par une police locale (lot 5) », « `--filigrane` déclarée (lot 5) » et « IBAN d'exemple invalide corrigé (lot 5) ».
- Historique : - v0.7.1 (Lot 5, 04/11/2026) : JetBrains Mono embarquée en local, `--filigrane` déclarée dans le `:root`, IBAN d'exemple corrigé.

decisions.md (déjà écrit à la clôture) :
- D-005, D-006 et D-007, voir le journal.

## Essais sur documents réels à prévoir

À faire sur le Mac, avec `uv run extracteur.py` puis `http://localhost:8000/extractorultimator.html` :
- Onglet Réseau des outils de développement du navigateur : après rechargement, aucune requête vers un autre hôte que localhost. Résultat attendu : zéro requête externe.
- RIB de démo et passeport de démo : les valeurs extraites s'affichent en police à chasse fixe, graisses 400 et 500 correctes, et les niveaux de fiabilité sont identiques à ceux d'avant le lot.
- Fenêtre du terminal pendant une extraction : le nom du fichier n'apparaît plus.
- Fond de la page d'accueil de l'app : la guilloche (`#guilloche`, opacité 0,35) reste discrète avec la valeur choisie pour `--filigrane`. Voir Risques.

## Risques et points d'attention

- `--filigrane` n'est déclarée nulle part aujourd'hui. Pour un attribut SVG `stroke`, une variable non définie donne l'absence de trait, donc la guilloche est probablement invisible depuis le début. La déclarer la fait apparaître. L'agent Code choisit une valeur discrète de la palette, note dans la passation le rendu avant / après, et Gabriel valide visuellement. Si le rendu ne lui plaît pas, retour au workshop.
- Le message d'exception affiché à `extracteur.py:595` (`print(f"  Échec : {e}")`) n'est pas traité dans ce lot, car il n'a pas été discuté. Le Lint le remontera à relire (R13). L'agent Lint tranche s'il le tolère comme réserve, ou il escalade à Gabriel.
- Les deux IBAN de la landing (`lint/specimens.json`) ont 25 caractères : valides en mod-97, mais pas au format français (27 caractères). `iban_valide` les accepte, car son contrôle de longueur est large. Hors périmètre ici ; consigné dans `agent.md` section 6 pour un lot ultérieur.
- Le canvas Figma peut encore afficher l'ancien IBAN d'exemple. Hors dépôt, non traité.
- Licence de la police : JetBrains Mono est sous SIL Open Font License 1.1. Le fichier `OFL.txt` doit accompagner les fichiers de police dans le dépôt.
- Arrêt obligatoire à connaître : l'agent Code télécharge les fichiers de police une seule fois, depuis la source officielle de JetBrains Mono. Ce téléchargement est autorisé par ce brief. Il n'ajoute aucune ressource distante dans l'app.
