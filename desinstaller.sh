#!/usr/bin/env bash
#
# desinstaller.sh — Désinstallation de Scribo
#
# Ce script retire, une étape à la fois et TOUJOURS après confirmation :
#   1. le modèle Mistral mis en cache (~4 Go)
#   2. les dépendances Python installées par Scribo
#   3. (rappel) le dossier du projet, à supprimer soi-même
#
# Rien n'est supprimé sans que vous tapiez « o » (oui). Vous pouvez
# refuser chaque étape indépendamment. Fermez le terminal à tout moment
# pour tout annuler.
#
# Usage :  bash desinstaller.sh

set -u  # une variable non définie est une erreur (mais pas set -e : on gère nous-mêmes)

# — petites fonctions d'affichage —
titre()   { printf "\n\033[1m%s\033[0m\n" "$1"; }
info()    { printf "  %s\n" "$1"; }
ok()      { printf "  \033[32m✓ %s\033[0m\n" "$1"; }
skip()    { printf "  \033[33m→ %s\033[0m\n" "$1"; }

# demande une confirmation ; renvoie 0 si l'utilisateur répond oui
confirmer() {
  local reponse
  printf "  \033[1m%s\033[0m [o/N] " "$1"
  read -r reponse
  case "$reponse" in
    o|O|oui|OUI|Oui|y|Y|yes) return 0 ;;
    *) return 1 ;;
  esac
}

printf "\033[1m\n╔══════════════════════════════════════════╗\n"
printf   "║      Désinstallation de Scribo           ║\n"
printf   "╚══════════════════════════════════════════╝\033[0m\n"
info "Chaque suppression vous sera demandée. Rien n'est effacé sans votre accord."

# ─────────────────────────────────────────────────────────
# ÉTAPE 1 — le modèle en cache
# ─────────────────────────────────────────────────────────
titre "1 · Modèle Mistral en cache"

CACHE="$HOME/.cache/huggingface"
if [ -d "$CACHE" ]; then
  TAILLE=$(du -sh "$CACHE" 2>/dev/null | cut -f1)
  info "Trouvé : $CACHE  (taille : ${TAILLE:-inconnue})"
  info "Ce dossier contient les modèles téléchargés par Scribo (et par d'autres"
  info "outils utilisant Hugging Face, le cas échéant)."
  if confirmer "Supprimer ce cache ?"; then
    rm -rf "$CACHE" && ok "Cache supprimé." || skip "Échec de la suppression."
  else
    skip "Cache conservé."
  fi
else
  skip "Aucun cache trouvé (rien à supprimer)."
fi

# ─────────────────────────────────────────────────────────
# ÉTAPE 2 — les dépendances Python
# ─────────────────────────────────────────────────────────
titre "2 · Dépendances Python"
info "Scribo installe : mlx-lm, pdfplumber (et éventuellement ocrmac)."
info "⚠️  Ne les retirez que si AUCUN autre de vos projets ne s'en sert."

# on détecte la bonne commande pip
if command -v pip >/dev/null 2>&1; then
  PIP="pip"
elif python3 -m pip --version >/dev/null 2>&1; then
  PIP="python3 -m pip"
else
  PIP=""
fi

if [ -z "$PIP" ]; then
  skip "pip introuvable — étape ignorée."
else
  for paquet in mlx-lm pdfplumber ocrmac; do
    if $PIP show "$paquet" >/dev/null 2>&1; then
      if confirmer "Désinstaller $paquet ?"; then
        $PIP uninstall -y "$paquet" >/dev/null 2>&1 && ok "$paquet désinstallé." || skip "Échec pour $paquet."
      else
        skip "$paquet conservé."
      fi
    else
      skip "$paquet non installé."
    fi
  done
fi

# ─────────────────────────────────────────────────────────
# ÉTAPE 3 — le dossier du projet
# ─────────────────────────────────────────────────────────
titre "3 · Dossier du projet"
DOSSIER="$(cd "$(dirname "$0")" && pwd)"
info "Le projet se trouve dans :"
info "  $DOSSIER"
info "Un script ne peut pas se supprimer proprement lui-même pendant qu'il tourne."
info "Pour finir le nettoyage, fermez ce terminal puis glissez ce dossier"
info "dans la corbeille depuis le Finder."

titre "Terminé."
info "Merci d'avoir essayé Scribo."
printf "\n"
