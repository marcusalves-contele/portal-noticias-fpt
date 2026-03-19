#!/bin/bash
# sync_knowledge.sh — copia docs do vault e design system para knowledge/
# Re-executar sempre que os docs fonte forem atualizados.

set -e

VAULT="/Users/marcofassa/Documents/obsidian-marco/DOCS"
DESIGN_SYSTEM="/Users/marcofassa/Documents/assistant-sexta-feira/data/design-system"
THUMB_PROMPTS="/Users/marcofassa/Documents/growth-contele/prism-os/thumbnail-ai-creator/prompts"
DEST="$(dirname "$0")/knowledge"

mkdir -p "$DEST"

echo "Sincronizando knowledge/..."

# Vault docs
cp "$VAULT/brand-fpt-agent.md"                          "$DEST/brand-fpt-agent.md"
cp "$VAULT/brand-fpt.md"                                "$DEST/brand-fpt.md"
cp "$VAULT/sistema-thumbnails-ai.md"                    "$DEST/sistema-thumbnails-ai.md"
cp "$VAULT/thumbnail-ai-creator.md"                     "$DEST/thumbnail-ai-creator.md"
cp "$VAULT/entrevista-arquetipo-julio-PROCESSADO.md"    "$DEST/entrevista-arquetipo-julio-PROCESSADO.md"
cp "$VAULT/prism-os.md"                                 "$DEST/prism-os.md"
cp "$VAULT/nutella-plano-producao-master.md"            "$DEST/nutella-plano-producao-master.md"
cp "$VAULT/playbook-conteudo-contele-2026.md"           "$DEST/playbook-conteudo-contele-2026.md"
cp "$VAULT/estrategia-instagram-2026.md"                "$DEST/estrategia-instagram-2026.md"

# Design system
cp "$DESIGN_SYSTEM/contele-fleet/README.md"             "$DEST/design-system-fleet.md"
cp "$DESIGN_SYSTEM/contele/brand-manual-2024.md"        "$DEST/brand-manual-2024.md"

# Templates de prompt
cp "$THUMB_PROMPTS/template_podvisitar.md"              "$DEST/template-podvisitar.md"

echo "knowledge/ atualizado com $(ls "$DEST" | wc -l | tr -d ' ') arquivos:"
ls "$DEST"
