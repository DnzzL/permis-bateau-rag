# Examen blanc (révision interleavée) — Leçon 10

Leçon 10 : examen blanc en conditions réelles, 40 questions tous chapitres mélangés, correction différée, seuil 35/40 (5 erreurs max).

**Ce qui a été créé :**
- Nouveau composant réutilisable `assets/exam.js` : mode examen à correction DIFFÉRÉE (≠ quiz.js feedback immédiat). Sélection unique, bouton « Corriger », score + verdict ADMIS/RECALÉ, bilan par thème (⚠️ si < 70 %), bouton recommencer. Configurable via `data-max-errors`.
- Styles partagés ajoutés à `assets/permis.css` (.exam-bar sticky, .exam-question, .topic-chip, .exam-btn, .exam-result pass/fail).
- Leçon `0010-revision-examen-blanc.html` : 40 questions interleavées, chacune taguée `data-topic` pour le bilan.

**Répartition (calquée sur le poids réel de l'examen) :**
Priorités 8 · Feux 5 · Balisage 5 · Météo 5 · Sécurité 5 · Réglementation 5 · Carte & navigation 4 · Mouillage & manœuvres 3 = 40.

**Principes pédagogiques appliqués :**
- Interleaving (mélange des thèmes) + retrieval practice (répondre de mémoire) + correction différée (effet test).
- Bilan par thème → dirige la révision vers les points faibles.
- Reco à l'utilisateur : refaire l'examen à J+2-3 puis J+7 (espacement) pour la storage strength.

**Conséquences / état du parcours :**
- Parcours côtier théorique complet (leçons 1-9) + examen blanc (10). L'utilisateur a de quoi s'auto-évaluer avant l'examen réel.
- Prochaine piste : volet FLUVIAL (objectif secondaire de la mission) — leçon 11 référencée dans la nav comme 0011-navigation-fluviale.html (lien teaser, pas encore créé).
- Idée future : un 2e jeu de 40 questions (variantes) pour éviter la mémorisation des items et garder l'effort de récupération réel.
