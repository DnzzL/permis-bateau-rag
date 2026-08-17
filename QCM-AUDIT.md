# QCM-AUDIT — Audit de conformité factuelle des 165 QCM

> Projet : *Permis bateau* (RAG) — vérification des réponses (`correct_index`) contre les sources officielles.

**Date de l'audit :** session en cours — les textes réglementaires ont été vérifiés dans leur version applicable à la date du contrôle (Division 240 modifiée par l'arrêté du 21 mai 2026, publiée au JORF du 08/06/2026).

**Sources officielles consultées :** Division 240 (PDF officiel JORF 08/06/2026), RIPAM/COLREG 1972, CEVNI (CEE-ONU), arrêté du 21 juillet 2011 (permis plaisance), code des transports, code du sport, Météo-France, mer.gouv.fr, VNF, SHOM. Pages secondaires fiables (organismes de formation, plaisance, VNF) citées pour les éléments de pratique enseignée.

## Résumé exécutif

- **Total : 165 QCM** (leçons 0001–0015 + examens blancs, base DuckDB `qcm`).
- **161 ✅ conformes** — dont 5 conformes avec nuance signalée.
- **2 ❌ faux** (ID 28, ID 35) — **corrigés** dans les fichiers HTML des leçons (uniquement les blocs QCM).
- **2 ⚠️ douteux / non vérifiables objectivement** (ID 2, ID 85) — opinions ou recommandations d'usage sans référence réglementaire.
- **5 doublons de questions** détectés (voir section Doublons).

**Indicateur : 163/165 ✓ après correction** (161 ✅ + 2 ❌ corrigées → ✅ ; restent 2 ⚠️ d'ordre pédagogique).


---

## 0001-vue-ensemble-permis — Vue d'ensemble du permis plaisance

**Vérifié contre :** Permis plaisance : âge (16 ans), puissance (4,5 kW / 6 ch), option côtière 6 milles, déroulement (5 h théorie, 40 questions).

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 0 | Jusqu'à quelle distance d'un abri le permis côtier permet-il de navi… | ✅ | Conforme — Permis plaisance | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 1 | Combien de questions comporte le QCM théorique du permis côtier ? | ✅ | Conforme — Permis plaisance | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 2 | Quel est le thème le plus important du programme du permis côtier ? | ⚠️ | Question d'opinion pédagogique : aucune norme ne classe « le thème le plus important » du progr… | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 3 | À partir de quel âge peut-on passer le permis bateau côtier ? | ✅ | Conforme — Permis plaisance | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |

---

## 0002-regles-route-priorites — Règles de route et priorités

**Vérifié contre :** RIPAM (COLREG 1972) : règles 13 (rattrapage), 14 (face à face), 15 (route qui se croise), 18 (voilier/moteur), 12 et 16 (règles entre voiliers).

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 4 | En face à face entre deux bateaux à moteur, que fait chaque bateau ? | ✅ | Conforme — RIPAM (COLREG 1972) | https://www.imo.org/en/About/Conventions/Contents/Conventions/Pages/COLREG.aspx |
| 5 | Deux bateaux à moteur se croisent. Qui doit dérouter ? | ✅ | Conforme — RIPAM (COLREG 1972) | https://www.imo.org/en/About/Conventions/Contents/Conventions/Pages/COLREG.aspx |
| 6 | Quand un bateau en rattrape un autre, qui déroute ? | ✅ | Conforme — RIPAM (COLREG 1972) | https://www.imo.org/en/About/Conventions/Contents/Conventions/Pages/COLREG.aspx |
| 7 | Un voilier vent tribord croise un voilier vent bâbord. Qui est prior… | ✅ | Conforme — RIPAM (COLREG 1972) | https://www.imo.org/en/About/Conventions/Contents/Conventions/Pages/COLREG.aspx |
| 8 | Quelle manœuvre est correcte dans un face à face ? | ✅ | Nuance : la manœuvre (virement à tribord) est exigée par la règle 14 RIPAM ; le signal sonore « 1 son bref » est facultatif (règle 34) — formulation pédagogique acceptable. | https://www.imo.org/en/About/Conventions/Contents/Conventions/Pages/COLREG.aspx |

---

## 0003-feux-navigation — Feux et signalisation de nuit

**Vérifié contre :** RIPAM : règles 20-21 (perte de vue des feux), 22 (portée), 23 (navires à moteur), 25 (voiliers), 26 (pêche), 27 (non maître de sa manœuvre), 30 (mouillage).

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 9 | De quelle couleur est le feu de navigation à bâbord (côté gauche) ? | ✅ | Conforme — RIPAM | https://www.imo.org/en/About/Conventions/Contents/Conventions/Pages/COLREG.aspx |
| 10 | Vous voyez un seul feu blanc la nuit. Que peut-ce être ? | ✅ | Formulation « peut être » : conforme (règle 30 RIPAM : mouillage = feu blanc visible 360°). Le feedback signale lui-même le piège du feu de poupe d'un navire qui s'éloigne. | https://www.imo.org/en/About/Conventions/Contents/Conventions/Pages/COLREG.aspx |
| 11 | Quel feu n'est PAS présent sur un voilier naviguant à la voile ? | ✅ | Conforme — RIPAM | https://www.imo.org/en/About/Conventions/Contents/Conventions/Pages/COLREG.aspx |
| 12 | Vous voyez simultanément un feu rouge, un feu vert et un feu blanc. … | ✅ | Conforme — RIPAM | https://www.imo.org/en/About/Conventions/Contents/Conventions/Pages/COLREG.aspx |
| 13 | Que signifient 2 feux rouges superposés ? | ✅ | Conforme — RIPAM | https://www.imo.org/en/About/Conventions/Contents/Conventions/Pages/COLREG.aspx |

---

## 0004-balisage-maritime — Balisage maritime (IALA A)

**Vérifié contre :** Système de balisage maritime IALA région A : latérales (région A : bouée rouge à bâbord en venant du large), cardinales (éclats 3/6/9), danger isolé, eaux saines, marques spéciales.

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 14 | En venant du large vers un port, où se tient la bouée rouge ? | ✅ | Conforme — Système de balisage maritime IALA région A | https://www.shom.fr/les-activites/navigation/balisage |
| 15 | Quelle est la forme du sommet d'une bouée bâbord ? | ✅ | Conforme — Système de balisage maritime IALA région A | https://www.shom.fr/les-activites/navigation/balisage |
| 16 | Une bouée cardinale Nord signale un danger. Où est le danger ? | ✅ | Conforme — Système de balisage maritime IALA région A | https://www.shom.fr/les-activites/navigation/balisage |
| 17 | Combien d'éclats groupés pour une bouée cardinale Ouest ? | ✅ | Conforme — Système de balisage maritime IALA région A | https://www.shom.fr/les-activites/navigation/balisage |
| 18 | Quelle bouée a des bandes horizontales noires et rouges + 2 sphères … | ✅ | Conforme — Système de balisage maritime IALA région A | https://www.shom.fr/les-activites/navigation/balisage |
| 19 | Une bouée à bandes verticales rouges et blanches + sphère rouge indi… | ✅ | Conforme — Système de balisage maritime IALA région A | https://www.shom.fr/les-activites/navigation/balisage |

---

## 0005-meteo-vents — Météo et vents

**Vérifié contre :** Échelle Beaufort (force 6 = vent frais), vents méditerranéens (mistral NO, levant E, sirocco SE), loi de Buys-Ballot, isobares, cumulonimbus.

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 20 | Q1. Quel vent méditerranéen est caractérisé par sa violence, sa fraî… | ✅ | Conforme — Échelle Beaufort (force 6 = vent frais), vents méditerranéens (mistral NO, levant E, sirocco SE), loi de Buys-Ballot, isobares, cumulonimbus. | https://meteofrance.com/meteo-a-z/quest-ce-que-le-vent |
| 21 | Q2. Selon la loi de Buys-Ballot (hémisphère nord), si vous tournez l… | ✅ | Conforme — Échelle Beaufort (force 6 = vent frais), vents méditerranéens (mistral NO, levant E, sirocco SE), loi de Buys-Ballot, isobares, cumulonimbus. | https://meteofrance.com/meteo-a-z/quest-ce-que-le-vent |
| 22 | Q3. Quel vent méditerranéen vient de l'Est et apporte généralement d… | ✅ | Conforme — Échelle Beaufort (force 6 = vent frais), vents méditerranéens (mistral NO, levant E, sirocco SE), loi de Buys-Ballot, isobares, cumulonimbus. | https://meteofrance.com/meteo-a-z/quest-ce-que-le-vent |
| 23 | Q4. À partir de quelle force Beaufort considère-t-on que le vent est… | ✅ | Conforme — Échelle Beaufort (force 6 = vent frais), vents méditerranéens (mistral NO, levant E, sirocco SE), loi de Buys-Ballot, isobares, cumulonimbus. | https://meteofrance.com/meteo-a-z/quest-ce-que-le-vent |
| 24 | Q5. Quel nuage annonce un danger immédiat en Méditerranée avec risqu… | ✅ | Conforme — Échelle Beaufort (force 6 = vent frais), vents méditerranéens (mistral NO, levant E, sirocco SE), loi de Buys-Ballot, isobares, cumulonimbus. | https://meteofrance.com/meteo-a-z/quest-ce-que-le-vent |
| 25 | Q6. Un vent du sud-est, chaud, parfois chargé de sable, qui traverse… | ✅ | Conforme — Échelle Beaufort (force 6 = vent frais), vents méditerranéens (mistral NO, levant E, sirocco SE), loi de Buys-Ballot, isobares, cumulonimbus. | https://meteofrance.com/meteo-a-z/quest-ce-que-le-vent |
| 26 | Q7. Vrai ou faux : en Méditerranée, un vent de secteur nord apporte … | ✅ | En Méditerranée les vents de secteur nord (mistral, tramontane) sont secs ; la pluie vient des secteurs sud/est. | https://meteofrance.com/meteo-a-z/quest-ce-que-le-vent |
| 27 | Q8. Sur une carte météo, comment reconnaître une zone de vent fort ? | ✅ | Conforme — Échelle Beaufort (force 6 = vent frais), vents méditerranéens (mistral NO, levant E, sirocco SE), loi de Buys-Ballot, isobares, cumulonimbus. | https://meteofrance.com/meteo-a-z/quest-ce-que-le-vent |

---

## 0006-securite-equipements — Sécurité et équipements

**Vérifié contre :** Division 240 (règlement annexé à l'arrêté du 23 novembre 1987, modifiée par arrêté du 21 mai 2026, JORF 08/06/2026) : armements basique/côtier/semi-hauturier, canal 16, MAYDAY/PAN PAN, feux de détresse.

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 28 | Q1. Quel est l'équipement obligatoire pour naviguer jusqu'à 6 milles… | ❌ | Erreur corrigée : la VHF fixe n'est obligatoire qu'à partir de 6 milles (armement semi-hauturie… | https://www.mer.gouv.fr/cap-nautique/permis-bateau |
| 29 | Q2. Sur quel canal VHF devez-vous appeler en cas de détresse ? | ✅ | Conforme — Division 240 (règlement annexé à l'arrêté du 23 novembre 1987, modifiée par arrêté du 21 mai 2026, JORF 08/06/2026) | https://www.mer.gouv.fr/cap-nautique/permis-bateau |
| 30 | Q3. Combien de fusées devez-vous tirer pour constituer un signal de … | ✅ | Conforme — Division 240 (règlement annexé à l'arrêté du 23 novembre 1987, modifiée par arrêté du 21 mai 2026, JORF 08/06/2026) | https://www.mer.gouv.fr/cap-nautique/permis-bateau |
| 31 | Q4. Quand devez-vous vérifier la date d'expiration des fusées de dét… | ✅ | Conforme — Division 240 (règlement annexé à l'arrêté du 23 novembre 1987, modifiée par arrêté du 21 mai 2026, JORF 08/06/2026) | https://www.mer.gouv.fr/cap-nautique/permis-bateau |
| 32 | Q5. Dans une situation d'homme à la mer, quelle est la première acti… | ✅ | Conforme — Division 240 (règlement annexé à l'arrêté du 23 novembre 1987, modifiée par arrêté du 21 mai 2026, JORF 08/06/2026) | https://www.mer.gouv.fr/cap-nautique/permis-bateau |
| 33 | Q6. Quelle est la différence entre MAYDAY et PAN PAN ? | ✅ | Conforme — Division 240 (règlement annexé à l'arrêté du 23 novembre 1987, modifiée par arrêté du 21 mai 2026, JORF 08/06/2026) | https://www.mer.gouv.fr/cap-nautique/permis-bateau |
| 34 | Q7. Quel signal de détresse est le plus approprié de jour ? | ✅ | Conforme — Division 240 (règlement annexé à l'arrêté du 23 novembre 1987, modifiée par arrêté du 21 mai 2026, JORF 08/06/2026) | https://www.mer.gouv.fr/cap-nautique/permis-bateau |
| 35 | Q8. Dans quelle direction devez-vous tirer une fusée de détresse ? | ❌ | Erreur corrigée : une fusée parachute se tire FACE au vent (~45-60°) pour que le parachute se d… | https://www.mer.gouv.fr/cap-nautique/permis-bateau |

---

## 0007-reglementation — Réglementation (mer)

**Vérifié contre :** Arrêté du 21 juillet 2011 (permis, âges, puissance), code des transports, préfectures maritimes (bande des 300 m : 5 nœuds), code du sport (plongée : 100 m du pavillon Alpha), immatriculation depuis 2022.

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 36 | Q1. Quelle est la vitesse maximale autorisée dans la bande des 300 m… | ✅ | Conforme — Arrêté du 21 juillet 2011 (permis, âges, puissance), code des transports, préfectures maritimes (bande des 300 m | https://www.legifrance.gouv.fr/loda/id/JORFTEXT000024497884/ |
| 37 | Q2. Comment doit-on traverser la bande des 300 mètres pour rejoindre… | ✅ | Conforme — Arrêté du 21 juillet 2011 (permis, âges, puissance), code des transports, préfectures maritimes (bande des 300 m | https://www.legifrance.gouv.fr/loda/id/JORFTEXT000024497884/ |
| 38 | Q3. Que signale le pavillon Alpha hissé sur un bateau ? | ✅ | Conforme — Arrêté du 21 juillet 2011 (permis, âges, puissance), code des transports, préfectures maritimes (bande des 300 m | https://www.legifrance.gouv.fr/loda/id/JORFTEXT000024497884/ |
| 39 | Q4. Quelle distance minimale devez-vous respecter autour d'une marqu… | ✅ | Conforme — Arrêté du 21 juillet 2011 (permis, âges, puissance), code des transports, préfectures maritimes (bande des 300 m | https://www.legifrance.gouv.fr/loda/id/JORFTEXT000024497884/ |
| 40 | Q5. À partir de quelle puissance moteur le permis devient-il obligat… | ✅ | Conforme — Arrêté du 21 juillet 2011 (permis, âges, puissance), code des transports, préfectures maritimes (bande des 300 m | https://www.legifrance.gouv.fr/loda/id/JORFTEXT000024497884/ |
| 41 | Q6. Quel est l'âge minimum pour passer le permis côtier ? | ✅ | Conforme — Arrêté du 21 juillet 2011 (permis, âges, puissance), code des transports, préfectures maritimes (bande des 300 m | https://www.legifrance.gouv.fr/loda/id/JORFTEXT000024497884/ |
| 42 | Q7. Sur quel fond est-il interdit de mouiller en Méditerranée ? | ✅ | Conforme — Arrêté du 21 juillet 2011 (permis, âges, puissance), code des transports, préfectures maritimes (bande des 300 m | https://www.legifrance.gouv.fr/loda/id/JORFTEXT000024497884/ |
| 43 | Q8. Quel document identifie officiellement votre navire depuis 2022 … | ✅ | Conforme — Arrêté du 21 juillet 2011 (permis, âges, puissance), code des transports, préfectures maritimes (bande des 300 m | https://www.legifrance.gouv.fr/loda/id/JORFTEXT000024497884/ |

---

## 0008-mouillage-manoeuvres — Mouillage et manœuvres

**Vérifié contre :** Pratiques de manœuvre enseignées aux examens : mouillage (3× la profondeur par temps calme), approche du quai contre le vent, nœud de chaise, vérification de la tenue par amers.

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 44 | Q1. Quelle longueur de chaîne filer par temps calme ? | ✅ | Conforme — Pratiques de manœuvre enseignées aux examens | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 45 | Q2. Comment aborder un quai en sécurité ? | ✅ | Conforme — Pratiques de manœuvre enseignées aux examens | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 46 | Q3. Sur quel fond faut-il éviter de mouiller ? | ✅ | Conforme — Pratiques de manœuvre enseignées aux examens | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 47 | Q4. Comment vérifier que l'ancre tient bien ? | ✅ | Conforme — Pratiques de manœuvre enseignées aux examens | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 48 | Q5. À quoi servent les pare-battages ? | ✅ | Conforme — Pratiques de manœuvre enseignées aux examens | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 49 | Q6. Quel nœud forme une boucle qui ne se serre pas ? | ✅ | Conforme — Pratiques de manœuvre enseignées aux examens | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |

---

## 0009-carte-navigation — Carte et navigation

**Vérifié contre :** Carte marine (SHOM) : mille nautique = 1 852 m, sonde (profondeur), sonde soulignée (zone découvrante), échelle des latitudes, cap vs route, heure de marée.

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 50 | Q1. À combien de mètres correspond un mille nautique ? | ✅ | Conforme — Carte marine (SHOM) | https://www.shom.fr/ |
| 51 | Q2. Sur quelle échelle mesure-t-on une distance sur la carte ? | ✅ | Conforme — Carte marine (SHOM) | https://www.shom.fr/ |
| 52 | Q3. Où lit-on la latitude sur une carte marine ? | ✅ | Conforme — Carte marine (SHOM) | https://www.shom.fr/ |
| 53 | Q4. À 10 nœuds, combien de temps pour parcourir 30 milles ? | ✅ | Conforme — Carte marine (SHOM) | https://www.shom.fr/ |
| 54 | Q5. Que représente une « sonde » sur la carte ? | ✅ | Conforme — Carte marine (SHOM) | https://www.shom.fr/ |
| 55 | Q6. Quelle est la différence entre le cap et la route ? | ✅ | Conforme — Carte marine (SHOM) | https://www.shom.fr/ |
| 56 | Q7. Sonde de 4 m sur la carte, marée de 1 m à cet instant. Quelle es… | ✅ | Conforme — Carte marine (SHOM) | https://www.shom.fr/ |
| 57 | Q8. Que signifie une sonde dont le chiffre est souligné sur la carte… | ✅ | Conforme — Carte marine (SHOM) | https://www.shom.fr/ |

---

## 0010-revision-examen-blanc — Examen blanc côtier

**Vérifié contre :** Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009).

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 58 | Deux bateaux à moteur se croisent avec risque d'abordage. Qui doit s… | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 59 | De quelle couleur est le feu de navigation à bâbord ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 60 | En entrant dans un port, de quel côté laissez-vous la bouée rouge ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 61 | Le mistral est un vent… | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 62 | Sur quel canal VHF lance-t-on un appel de détresse ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 63 | Quelle est la vitesse maximale dans la bande des 300 mètres ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 64 | Combien vaut un mille nautique ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 65 | Quelle longueur de chaîne filer par temps calme ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 66 | Deux bateaux à moteur arrivent face à face. Que fait chacun ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 67 | La nuit, vous voyez un feu rouge, un feu vert et un feu blanc ensemb… | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 68 | Quelle est la forme d'une marque latérale de tribord ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 69 | Un anticyclone est associé à… | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 70 | Les signaux de détresse se font par séries de… | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 71 | Comment traverse-t-on la bande des 300 m pour rejoindre le large ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 72 | Sur quelle échelle mesure-t-on une distance sur la carte ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 73 | Comment aborder un quai en sécurité ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 74 | Lors d'un dépassement, qui doit s'écarter ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 75 | Un seul feu blanc visible tout autour (360°) signale le plus souvent… | ✅ | Conforme : feu blanc 360° = bateau au mouillage (règle 30 RIPAM), avec le même piège de feu de poupe rappelé dans le feedback. | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 76 | De quel côté passe-t-on une marque cardinale Sud ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 77 | Quel nuage annonce un orage ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 78 | Que signifie l'appel « MAYDAY » ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 79 | Quelle distance respecter autour d'une marque de plongeur ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 80 | Comment obtient-on la hauteur d'eau réelle à un instant donné ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 81 | À quoi servent les pare-battages ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 82 | Un voilier tribord amure croise un voilier bâbord amure. Qui est pri… | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 83 | Que signifient deux feux rouges superposés ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 84 | Combien d'éclats groupés pour une cardinale Ouest ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 85 | Quelle est la limite Beaufort raisonnable pour un petit bateau ? | ⚠️ | Recommandation d'usage, aucune obligation réglementaire ne fixe une « limite Beaufort raisonnab… | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 86 | Homme à la mer : quelle est la toute première action ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 87 | À partir de quelle puissance le permis est-il obligatoire ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 88 | Que signifie une sonde soulignée sur la carte ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 89 | Deux voiliers de même amure : lequel est prioritaire ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 90 | Quel feu un voilier à la voile ne porte-t-il PAS ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 91 | Une bouée à bandes verticales rouges et blanches surmontée d'une sph… | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 92 | Dos au vent dans l'hémisphère nord, où se trouve la dépression ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 93 | Quel signal de détresse est le plus adapté de jour ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 94 | Sur quel fond est-il interdit de mouiller en Méditerranée ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 95 | Que signifie un seul coup de sirène court ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 96 | Un bateau à moteur et un voilier se croisent (hors dépassement). Qui… | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |
| 97 | Quelle obligation s'impose en permanence à tout navire ? | ✅ | Conforme — Récapitulatif des règles de route, feux, balisage, météo, sécurité, réglementation et cartographie (cf. sources des leçons 0001-0009). | https://www.mer.gouv.fr/le-permis-plaisance-permis-de-conduire-les-bateaux-de-plaisance-moteur |

---

## 0011-navigation-fluviale — Navigation fluviale (bases)

**Vérifié contre :** CEVNI (Code européen des voies de navigation intérieure) : rive droite en regardant l'aval, croisement bâbord/bâbord, balisage rouge rive droite, feux d'écluse, priorité au commerce.

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 98 | Comment définit-on la rive droite d'un fleuve ? | ✅ | Conforme — CEVNI (Code européen des voies de navigation intérieure) | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 99 | De quelle couleur est le balisage du côté de la rive droite ? | ✅ | Conforme — CEVNI (Code européen des voies de navigation intérieure) | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 100 | Que signifie un panneau fluvial bleu à pictogramme blanc ? | ✅ | Conforme — CEVNI (Code européen des voies de navigation intérieure) | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 101 | En rivière, de quel côté tient-on normalement ? | ✅ | Conforme — CEVNI (Code européen des voies de navigation intérieure) | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 102 | Quel feu d'écluse autorise l'entrée dans le sas ? | ✅ | Conforme — CEVNI (Code européen des voies de navigation intérieure) | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 103 | Face à une grande péniche de commerce, le bateau de plaisance doit… | ✅ | Conforme — CEVNI (Code européen des voies de navigation intérieure) | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 104 | En quelle unité sont indiquées les vitesses sur les voies fluviales … | ✅ | Conforme — CEVNI (Code européen des voies de navigation intérieure) | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |

---

## 0012-fluvial-reglementation-securite — Fluvial — réglementation et sécurité

**Vérifié contre :** Vignette VNF (> 5 m ou ≥ 9,9 CV / 7,29 kW), 0,5 g/l, gilets par personne, dispositif d'assèchement, batillage, titre de navigation, eaux intérieures exposées.

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 105 | Quand la vignette VNF est-elle obligatoire ? | ✅ | Conforme — Vignette VNF (> 5 m ou ≥ 9,9 CV / 7,29 kW), 0,5 g/l, gilets par personne, dispositif d'assèchement, batillage, titre de navigation, eaux intérieures exposées. | https://www.vnf.fr/vnf/accueil.vnf |
| 106 | Quel est le taux d'alcoolémie maximal autorisé à la barre ? | ✅ | Conforme — Vignette VNF (> 5 m ou ≥ 9,9 CV / 7,29 kW), 0,5 g/l, gilets par personne, dispositif d'assèchement, batillage, titre de navigation, eaux intérieures exposées. | https://www.vnf.fr/vnf/accueil.vnf |
| 107 | Combien d'équipements individuels de flottabilité faut-il à bord ? | ✅ | Conforme — Vignette VNF (> 5 m ou ≥ 9,9 CV / 7,29 kW), 0,5 g/l, gilets par personne, dispositif d'assèchement, batillage, titre de navigation, eaux intérieures exposées. | https://www.vnf.fr/vnf/accueil.vnf |
| 108 | Pourquoi faut-il limiter le batillage ? | ✅ | Conforme — Vignette VNF (> 5 m ou ≥ 9,9 CV / 7,29 kW), 0,5 g/l, gilets par personne, dispositif d'assèchement, batillage, titre de navigation, eaux intérieures exposées. | https://www.vnf.fr/vnf/accueil.vnf |
| 109 | À quoi sert le dispositif d'assèchement obligatoire ? | ✅ | Conforme — Vignette VNF (> 5 m ou ≥ 9,9 CV / 7,29 kW), 0,5 g/l, gilets par personne, dispositif d'assèchement, batillage, titre de navigation, eaux intérieures exposées. | https://www.vnf.fr/vnf/accueil.vnf |
| 110 | Quel document, avec le permis, identifie le bateau ? | ✅ | Conforme — Vignette VNF (> 5 m ou ≥ 9,9 CV / 7,29 kW), 0,5 g/l, gilets par personne, dispositif d'assèchement, batillage, titre de navigation, eaux intérieures exposées. | https://www.vnf.fr/vnf/accueil.vnf |
| 111 | Quel équipement s'ajoute en eaux intérieures « exposées » ? | ✅ | Conforme — Vignette VNF (> 5 m ou ≥ 9,9 CV / 7,29 kW), 0,5 g/l, gilets par personne, dispositif d'assèchement, batillage, titre de navigation, eaux intérieures exposées. | https://www.vnf.fr/vnf/accueil.vnf |

---

## 0013-panneaux-fluviaux — Panneaux fluviaux

**Vérifié contre :** CEVNI — panneaux : interdiction (fond blanc, bordure rouge, barre), obligation (chiffre = vitesse km/h), indication (bleu/blanc), hauteur (tirant d'air), losanges vert/blanc (chenal entre les marques), bac.

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 112 | Un panneau à fond blanc, bordure rouge et barre rouge en diagonale, … | ✅ | Conforme — CEVNI — panneaux | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 113 | Un panneau bleu avec un « P » blanc signifie… | ✅ | Conforme — CEVNI — panneaux | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 114 | Un panneau à bordure rouge portant le chiffre « 6 » indique… | ✅ | Conforme — CEVNI — panneaux | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 115 | Un panneau de hauteur limitée concerne… | ✅ | Conforme — CEVNI — panneaux | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 116 | Deux losanges vert et blanc signifient… | ✅ | Conforme — CEVNI — panneaux | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 117 | Pour interpréter un panneau fluvial, on regarde d'abord… | ✅ | Conforme — CEVNI — panneaux | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 118 | Un panneau bleu représentant un bac vous informe que… | ✅ | Conforme — CEVNI — panneaux | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |

---

## 0014-passage-ecluse — Passage d'écluse

**Vérifié contre :** RGP / CEVNI : feux d'écluse (rouge = attente, vert = entrée, rouge+vert = préparation), amarrage dans le sas (tour de bollard, filer/reprendre le mou), priorité du commerce.

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 119 | Comment tient-on son amarre dans le sas d'une écluse ? | ✅ | Conforme — RGP / CEVNI | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 120 | Dans une écluse montante, que fait-on de l'amarre pendant le remplis… | ✅ | Conforme — RGP / CEVNI | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 121 | Dans une écluse descendante, on doit… | ✅ | Conforme — RGP / CEVNI | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 122 | Quel signal autorise l'entrée dans le sas ? | ✅ | Conforme — RGP / CEVNI | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 123 | Une péniche de commerce et vous arrivez à l'écluse. Qui passe en pre… | ✅ | Conforme — RGP / CEVNI | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 124 | Avant d'entrer dans l'écluse, où place-t-on les pare-battages ? | ✅ | Conforme — RGP / CEVNI | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |

---

## 0015-fluvial-examen-blanc — Examen blanc fluvial

**Vérifié contre :** Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale.

| ID | Question (tronquée) | Verdict | Justification | Source |
|---|---|---|---|---|
| 125 | Comment définit-on la rive droite d'un cours d'eau ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 126 | Un panneau fluvial bleu à pictogramme blanc signifie… | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 127 | Quel feu d'écluse autorise l'entrée dans le sas ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 128 | En rivière, de quel côté tient-on normalement ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 129 | Combien de gilets de sauvetage faut-il à bord ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 130 | Qu'appelle-t-on le « batillage » ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 131 | Jusqu'à quelle longueur de bateau l'option eaux intérieures permet-e… | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 132 | Que signifie un seul son bref ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 133 | De quelle couleur est le balisage du côté de la rive droite ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 134 | Que signale, en général, un panneau à bordure rouge ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 135 | Que signifient deux feux rouges à l'écluse ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 136 | Le croisement habituel en rivière se fait… | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 137 | Quel équipement utilise-t-on contre un début d'incendie à bord ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 138 | Concernant les eaux usées et les hydrocarbures, leur rejet à l'eau e… | ✅ | Nuance : le rejet d'hydrocarbures est strictement interdit (réglementation sur les déchets des navires) ; les eaux usées doivent être collectées via les installations portuaires. Réponse enseignée conforme. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 139 | Quel est l'âge minimum pour le permis option eaux intérieures ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 140 | Que signifient deux sons brefs ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 141 | De quelle couleur est le balisage du côté de la rive gauche ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 142 | Un chiffre sur un panneau d'obligation indique… | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 143 | Que signifie un feu rouge et un feu vert allumés ensemble ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 144 | Face à une péniche de commerce, le bateau de plaisance doit… | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 145 | Quelqu'un tombe à l'eau. Quelle est la toute première action ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 146 | Pourquoi ralentir près des berges et des bateaux amarrés ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 147 | À partir de quelle puissance moteur le permis est-il obligatoire ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 148 | Que signale une série de sons très brefs ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 149 | Que signale une marque de balisage jaune ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 150 | Deux losanges vert et blanc signifient… | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 151 | Comment tient-on son amarre dans le sas d'une écluse ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 152 | Un bac traverse le fleuve devant vous. Que faites-vous ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 153 | Quel numéro de téléphone composer en cas d'urgence ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 154 | Que faire de ses déchets à bord ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 155 | Que faut-il pour naviguer sur les voies gérées par VNF ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 156 | « Aller vers l'aval », c'est aller… | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 157 | Quelle est la forme la plus courante des panneaux fluviaux ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 158 | Dans une écluse montante, que fait-on de l'amarre ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 159 | En quelle unité s'expriment les vitesses sur les voies fluviales ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 160 | Avec quoi évacue-t-on l'eau en cas de voie d'eau ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 161 | Quel document, avec le permis, doit-on pouvoir présenter à bord ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 162 | À quoi reconnaît-on un panneau d'interdiction ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 163 | Dans une écluse descendante, que fait-on de l'amarre ? | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |
| 164 | Concernant le nombre de personnes à bord, il faut… | ✅ | Conforme — Récapitulatif CEVNI/RGP/VNF (cf. sources des leçons 0011-0014) + 112 (numéro d'urgence européen), rejets interdits, capacité maximale. | https://unece.org/transport/documents/2021/02/standards/european-code-inland-waterways-cevni |

---

## Questions fausses corrigées

### ID 28 — lessons/0006-securite-equipements.html

- **Question :** Q1. Quel est l'équipement obligatoire pour naviguer jusqu'à 6 milles d'un abri ?
- **Avant :** réponses proposées ['Un téléphone portable étanche', 'Une VHF', 'Un radar', 'Un pilote automatique'] — `correct_index = 1` (faux)
- **Correction :** Erreur corrigée : la VHF fixe n'est obligatoire qu'à partir de 6 milles (armement semi-hauturier, art. 240-2.05). Pour la navigation côtière 2-6 M (art. 240-2.04), l'armement comprend matériel basique, bouée fer à cheval, EIF ≥ 100 N, 3 feux rouges à main, compas magnétique, cartes, RIPAM et document de balisage. Option [1] remplacée par « Un compas magnétique », index conservé.
### ID 35 — lessons/0006-securite-equipements.html

- **Question :** Q8. Dans quelle direction devez-vous tirer une fusée de détresse ?
- **Avant :** réponses proposées ['Face au vent', 'Verticalement, peu importe le vent', 'En direction de la côte', 'Sous le vent'] — `correct_index = 3` (faux)
- **Correction :** Erreur corrigée : une fusée parachute se tire FACE au vent (~45-60°) pour que le parachute se déploie et que l'engin ne revienne pas sur soi. Seul le fumigène (fumée) se lance sous le vent. correct_index 3 → 0, feedback réécrit.

---

## Questions douteuses / non vérifiables (⚠️ — non corrigées)

### ID 2 — lessons/0001-vue-ensemble-permis.html

- **Question :** Quel est le thème le plus important du programme du permis côtier ?
- **Réponse :** « Navigation (règles de route, priorités) »
- **Pourquoi ⚠️ :** Question d'opinion pédagogique : aucune norme ne classe « le thème le plus important » du programme. La réponse retenue (navigation) est conforme à l'usage des organismes de formation mais n'est pas vérifiable contre une source officielle.
### ID 85 — lessons/0010-revision-examen-blanc.html

- **Question :** Quelle est la limite Beaufort raisonnable pour un petit bateau ?
- **Réponse :** « Force 5 »
- **Pourquoi ⚠️ :** Recommandation d'usage, aucune obligation réglementaire ne fixe une « limite Beaufort raisonnable ». La valeur force 5 est celle couramment enseignée pour un petit bateau, mais elle est indicative.

---

## Questions dupliquées

Les leçons 0001–0014 contiennent des QCM repris à l'identique (libellé) dans les examens blancs (0010, 0015) avec un ordre d'options mélangé. Doublons stricts ou quasi stricts :

- **99 / 133** — « De quelle couleur est le balisage du côté de la rive droite ? » — identiques (options et index)
- **101 / 128** — « En rivière, de quel côté tient-on normalement ? » — mêmes options (ordre différent), même réponse — index cohérent
- **102 / 127** — « Quel feu d'écluse autorise l'entrée dans le sas ? » — **attention : correct_index diffère (1 vs 2)** car l'ordre des options a été mélangé ; le libellé correct (« Un feu vert ») est le même dans les deux — risque de confusion à l'export, pas d'erreur factuelle
- **116 / 150** — « Deux losanges vert et blanc signifient… » — mêmes réponses
- **119 / 151** — « Comment tient-on son amarre dans le sas d'une écluse ? » — mêmes réponses

De plus, ~20 questions des leçons 0002–0009 sont reprises dans l'examen blanc côtier (0010) avec des options mélangées (ex. 3/41/139, 4/66, 5/58, 9/59, 36/63, 39/79, 44/65, 50/64, 57/88, 87/147…) : doublons de contenu assumés (format « examen blanc »), pas des erreurs.

---

## Limites de l'audit

- Les éléments de **pratique enseignée** (×3 de profondeur pour le mouillage, bande des 300 m à 5 nœuds, limite « force 5 » pour petit bateau) ne reposent pas sur un texte unique : ils reprennent l'usage des formations agréées et des arrêtés préfectoraux littoraux (cf. REFERENCE-AUDIT.md).
- La base `qcm` (DuckDB) et les index RAG n'ont **pas** été re-générés (hors périmètre demandé) : les corrections d'ID 28/35 sont appliquées dans les fichiers HTML des leçons, qui sont la source de `extract.py`. Une régénération `extract.py` puis embarquement mettront à jour la DB.
- Légifrance étant protégé par anti-robots, les textes ont été vérifiés via le PDF officiel de la Division 240 et des pages gouvernementales (mer.gouv.fr, vnf.fr, douane.gouv.fr) et des pages fiables citées dans les tables.

---
*Généré automatiquement — audit des 165 QCM. Aucune modification hors blocs QCM des leçons et de ce fichier.*
