---
id: TASK-11
title: T11 — Couvrir les détails QCM manquants (top-3 ~63%)
status: Done
assignee: []
created_date: '2026-08-17 13:45'
updated_date: '2026-08-17 14:53'
labels: []
dependencies: []
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
FAIT — 3 livrables reference/ : carte-marine.html (nouveau, 7108 o), signaux-detresse.html (nouveau, 9712 o), signaux-bateaux-fluviaux.html (enrichi section 7 bis face-à-face/croisement/dépassement + 100 mètres). Photos QCM présentes textuellement (zone qui découvre à marée basse, 100 mètres, garder à vue, cap=dir. visée route=trajet réel, 1852 m, bâbord contre bâbord...). Re-extract + re-embed + graph rebuild (101 chunks) + benchmark seed 42 : coverage top-1 48→80%, top-3 63→90% (classic) et 65→92% (graph), pertinence 64→66%, refus 10/10. Source : SHOM, RIPAM Annexe IV, CEVNI/RGP, SNSM, mer.gouv.fr. "Italique variation non datée" non sourcé → omis. Fait hors périmètre : vents Le Levant (meteo.html déjà couvert).
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2 fiches détail (carte-marine.html, signaux-detresse.html) + enrichissement signaux-bateaux-fluviaux.html (sirènes face à face). Mesure de couverture corrigée (gold dans le contenu, pas la leçon source): 63%→90% top-3. Benchmark final: pertinence 64%, refus 10/10, coverage top-3 90%.
<!-- SECTION:NOTES:END -->
