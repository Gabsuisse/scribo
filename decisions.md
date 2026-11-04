# Scribo : journal des décisions

Date : 04/11/2026

Format : un identifiant D-NNN, la décision, la raison, le lot concerné. Une dérogation à une règle du lint est une décision comme une autre et s'écrit ici.

## Principes repris de l'historique du projet (baseline)

- D-000a : la souveraineté est non négociable, toute dépendance est embarquée en local. Raison : le zéro appel réseau est une promesse centrale du produit.
- D-000b : la vérification déterministe prime sur la confiance du modèle. Raison : une valeur validée par calcul ne peut pas être une hallucination.
- D-000c : la valeur affichée et la valeur vérifiée restent synchronisées. Raison : un bug a déjà estampillé "vérifié" une année de naissance fausse.
- D-000d : trois niveaux qualitatifs (Vérifié, Probable, À vérifier) plutôt que des pourcentages. Raison : plus honnête et plus actionnable.
- D-000e : fichier front unique en vanilla, pas de chaîne de build, pas de Tailwind. Raison : lancement en une commande.
- D-000f : installation par uv. Paquet .app différé car trop lourd avant l'objectif principal.
- D-000g : deux fichiers de documentation (agent.md, design.md) plutôt que quatre.

## Décisions du dispositif de travail

- D-001 (04/11/2026) : circuit workshop, validation, clôture, agent Code, agent Lint, dépôt Git. Le Lint renvoie une seule fois au Code, puis escalade vers Gabriel (décision dans le Lint ou nouveau workshop). Statut : décidé.
- D-002 (04/11/2026) : "déposer dans Git" signifie pousser une branche dédiée au lot et ouvrir une PR, sans fusion automatique. Raison : voir le diff complet avant fusion. Statut : décidé par Gabriel le 04/11/2026 (option A).
- D-003 (04/11/2026) : tant que le produit est en 0.x, un changement cassant incrémente le minor. Le passage en 1.0.0 est une décision de Gabriel. Raison : convention semver pour la série 0.x. Statut : décidé par Gabriel le 04/11/2026 (option B). Cette règle remplace, pour Scribo, la règle générale qui réserve le major aux changements cassants.
- D-004 (04/11/2026) : un projet Claude dédié à Scribo, séparé de "Produit de design". Raison : instructions propres, contexte non dilué. Statut : décidé.
