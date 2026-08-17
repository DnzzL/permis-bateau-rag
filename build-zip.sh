#!/usr/bin/env bash
# Génère un zip contenant uniquement le site statique déployable.
# Usage : ./build-zip.sh
set -euo pipefail
cd "$(dirname "$0")"

OUT="permis-plaisance-site.zip"
rm -f "$OUT"

# Contenu publié : l'entrée, la page 404, les assets, leçons, fiches, images
# et .nojekyll (pour GitHub Pages). Tout le reste (docs de travail, config git,
# fichiers macOS) est exclu.
zip -r -X "$OUT" \
  index.html \
  404.html \
  .nojekyll \
  assets \
  lessons \
  reference \
  ./*.png \
  -x '*.DS_Store' >/dev/null

echo "✅ $OUT créé ($(du -h "$OUT" | cut -f1))"
echo "   Déploie-le en le glissant sur https://app.netlify.com/drop"
