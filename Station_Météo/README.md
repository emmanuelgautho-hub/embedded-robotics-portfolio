# Station Météo Instrumentée (LabVIEW)

Ce projet consiste en la réalisation d'une application d'acquisition, de traitement de données et d'interface homme-machine (IHM) pour une station météo multi-capteurs développée sous LabVIEW. L'objectif principal était de concevoir une interface ergonomique permettant le suivi en temps réel, l'analyse statistique et l'archivage des données météorologiques.

---

## Fonctionnalités par Capteur

### 1. Gestion de la Température
* **Affichage & Calculs :** Affichage de la température en temps réel et calcul automatique du temps passé hors des limites saisonnières définies.
* **Graphique Temps Réel :** Visualisation de la mesure en continu avec affichage des lignes de limites haute et basse directement sur le graphe.
* **Analyse Temporelle :** Graphiques historiques montrant l'évolution de la température sur plusieurs échelles de temps : journée, semaine, mois et année.
* **Navigation :** Possibilité de changer manuellement la date d'affichage de la fenêtre pour consulter l'historique.
* **Sauvegarde :** Enregistrement continu des températures mesurées.

### 2. Girouette (Direction du Vent)
* **Affichage :** Rendu de la valeur brute de la girouette, affichage de la direction sous forme de chaîne de caractères (Nord, Sud, Est, Ouest, etc.) et intégration d'une boussole visuelle.
* **Graphique :** Visualisation en temps réel de l'évolution de la direction.
* **Sauvegarde :** Enregistrement de l'historique des directions du vent.

### 3. Compteur (Identification & Statut)
* **Affichage de la Station :** Rendu numérique (Integer) du numéro de la station et affichage binaire sous forme d'indicateurs LED.
* **Sauvegarde :** Enregistrement du numéro d'identification de la station dans la base de données.

### 4. Anémomètre (Vitesse du Vent)
* **Mesures & Graphique :** Affichage de la valeur instantanée et tracé d'un graphique temps réel.
* **Gestion des Pics :** Calcul automatique des pics de vitesse du vent et affichage visuel du pic directement sur le graphique.
* **Sauvegarde :** Enregistrement des mesures continues et des pics de vitesse détectés.

### 5. Pluviomètre (Précipitations)
* **Affichage & Conversion :** Rendu de la valeur du compteur brute et conversion automatique en millilitres (mL).
* **Alarmes :** Système d'alertes visuelles en cas de dépassement de seuils (alarme supérieure et alarme inférieure).
* **Graphique Temps Réel :** Tracé en continu avec visualisation des limites de seuils.
* **Analyse Temporelle & Navigation :** Graphiques d'évolution historiques (journée, semaine, mois, année) avec possibilité de changer la date de la fenêtre d'affichage.

---

## IHM, Ergonomie et Statistiques
* **Statistiques globales :** Module de traitement de données pour extraire les indicateurs clés sur les différents capteurs.
* **Interface Ergonomique :** Design de l'IHM pensé pour l'utilisateur, facilitant la lecture rapide des alarmes, de la boussole et des différentes fenêtres graphiques.

---

## Captures d'Écran et Visuels de l'IHM

*Pour intégrer tes images, remplace simplement le nom des fichiers entre parenthèses par tes propres captures d'écran après les avoir ajoutées dans ton dossier.*

### Interface Principale (Dashboard)
Voici l'IHM globale regroupant l'affichage des capteurs, la boussole et les indicateurs LED :
![Interface Principale de la Station Météo](ihm_principale.png)

### Graphiques et Historiques (Température & Pluviométrie)
Exemple des fenêtres graphiques permettant de changer de date et de visualiser les limites :
![Graphiques Temps Réel et Historiques](graphiques_mesures.png)

### Alarmes et Gestion des Pics
Visualisation du comportement du système lors d'un pic de vent ou d'un dépassement de seuil pluviométrique :
![Gestion des Alarmes et Pics](alarmes_et_pics.png)
