# 🐾 Navigation & Locomotion Autonome - Quadrupède Deep Robotics Lite3

> 📌 Projet académique de 5 semaines réalisé en équipe.
> Ce README fait office de rétrospective technique et d'analyse post-projet.

---

## 🎯 Objectifs & Contexte
L'objectif de ce sprint de 5 semaines était de doter le robot quadrupède **Lite3** d'une autonomie de franchissement d'escaliers en combinant des algorithmes de vision par ordinateur (IA) et des patterns de locomotion sous ROS2.

---

## 🏗️ Architecture du Code (Livré en fin de projet)

Le projet est structuré autour de deux modules principaux :

* 📂 `vision/` : Contient les pipelines de perception.
    * Modèles **YOLO** entraînés pour la détection et la localisation des structures d'escaliers en temps réel.
    * Modèle **Teachable Machine** utilisé pour la classification rapide des états d'approche du robot.
* 📂 `locomotion/` : Contient les nœuds ROS2 de contrôle et de marche développés de manière incrémentale.
    * *Montée aveugle :* Algorithme en boucle ouverte (open-loop) pour valider les patterns cinématiques de base.
    * *Montée avec LiDAR :* Nœud de contrôle ajustant l'alignement et la distance du robot face à la première marche grâce aux données de télémétrie.
    * *Montée escalier :* Comportement final combiné pour le franchissement d'obstacles verticaux répétitifs.

---

## 🔍 Rétrospective Technique & Limites Identifiées

Avec le recul et compte tenu de la contrainte stricte des 5 semaines de développement, une limite majeure de l'architecture finale a été identifiée :

Le système manque de robustesse face aux perturbations environnementales (changements brusques de luminosité impactant YOLO, ou masquage partiel du LiDAR). 

**Piste d'amélioration théorique :** Pour aller plus loin, il aurait fallu implémenter un nœud de fusion (type Filtre de Kalman Étendu ou SLAM RGB-D/LiDAR) afin de générer une grille d'élévation (*elevation map*) unique et dynamique, ou utiliser l'Apprentissage par Renforcement (RL) en simulation (IsaacLab/MuJoCo) pour entraîner une politique de marche globale face à l'inconnu.
