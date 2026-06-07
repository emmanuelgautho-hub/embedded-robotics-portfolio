## ⏱️ Contexte du Projet & Objectifs
Ce projet a été réalisé en un temps limité de **6 heures** dans le cadre d'une initiation au design électronique à l'ESIGELEC. 

**Objectifs principaux :**
* Prise en main rapide et en totale autonomie du logiciel **KiCad** (découverte de l'outil).
* Saisie de schéma électronique à partir d'un cahier des charges basique (Thermometre MSP430 / LM35).
* Association des composants à leurs empreintes physiques et initiation au placement sur PCB avec génération d'un rendu 3D.

---

## 📈 Compétences Validées durant ce TP
* **Apprentissage Express :** Capacité à appréhender un nouvel outil de CAO complexe (KiCad) et à sortir un livrable visuel en moins d'une journée.
* **Placement & Encombrement :** Réflexion sur la disposition des composants (piles CR2032, afficheur) pour optimiser l'espace et respecter les contraintes mécaniques du rendu 3D.
* **Compréhension du Multiplexage :** Modélisation théorique du câblage pour l'affichage dynamique 7 segments afin d'économiser les broches du microcontrôleur.

* ### ⚠️ Erreurs de conception identifiées (Revue post-projet)
Le but de ce TP de 6 heures étant une initiation rapide à l'outil KiCad, plusieurs erreurs de conception électronique ont été volontairement ou involontairement laissées dans cette version préliminaire :

1. **Alimentation du Microcontrôleur :** Les deux piles CR2032 délivrent une tension nominale de 6V (nécessaire pour le LM35 qui requiert un minimum de 4V). Cependant, le MSP430G2553 a une tension maximale absolue de 3.6V. Dans une version finale, l'ajout d'un régulateur de tension (LDO 3.3V) est indispensable pour protéger le microcontrôleur.
2. **Filtrage (Condensateurs de découplage) :** Aucun condensateur de découplage (100nF) n'a été intégré sur les lignes d'alimentation du MSP430 et du capteur. Sans eux, le bruit généré par le multiplexage de l'afficheur perturberait grandement les mesures de l'ADC.
3. **Statut du Routage :** Pour respecter le délai imparti de 6h, seul le placement des composants et la validation de l'encombrement 3D ont été réalisés. Les connexions électriques restent à l'état de "chevelu" (ratlines) et le routage des pistes de cuivre n'est pas finalisé.
