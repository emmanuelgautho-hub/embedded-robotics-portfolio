# embedded-robotics-portfolio
Portfolio de projets en Systèmes Embarqués, Robotique &amp; Vision IA - Emmanuel GAUTHO (ESIGELEC)
# Portfolio : Systèmes Embarqués et Robotique

Ce dépôt centralise mes principaux projets techniques et académiques. Je m'appelle Emmanuel Gautho, je suis actuellement étudiant en 2ème année de cycle ingénieur à l'ESIGELEC, spécialisé en Systèmes Embarqués. Mes travaux portent principalement sur la robotique mobile, le développement de micrologiciels (firmware) bas niveau et la vision par ordinateur.

## Projets

### Navigation de Robot Quadrupède (Deep Robotics Lite3 & ROS2)
Développement d'une stack de perception et de navigation autonome pour un robot quadrupède en environnement complexe.
* Conception et implémentation d'un système de détection d'escaliers basé sur une caméra Intel RealSense, OpenCV et YOLO.
* Traitement en temps réel des flux vidéo et de profondeur pour l'extraction des caractéristiques de l'environnement.
* Création de nœuds ROS2 personnalisés pour interfacer les données de vision avec le système de contrôle des moteurs du robot.

### Robot Mobile Autonome (MSP430)
Conception du firmware bare-metal pour un petit véhicule autonome focalisé sur l'évitement d'obstacles et le suivi de trajectoire.
* Interfaçage et traitement des signaux provenant de capteurs de distance à ultrasons.
* Gestion des actionneurs et des moteurs à courant continu via des signaux PWM et des interruptions matérielles.
* Optimisation du code C bas niveau pour fonctionner sous contraintes de ressources sur un microcontrôleur Texas Instruments MSP430G2553.

### Conception Électronique et Routage PCB (KiCad)
Réalisation complète du design matériel d'un système embarqué intégrant un microcontrôleur et plusieurs capteurs.
* Développement du schéma électronique complet et association des empreintes (footprints).
* Routage des pistes du circuit imprimé en veillant à l'intégrité des signaux et à la bonne distribution de la puissance.
* Génération des fichiers Gerber prêts pour la fabrication industrielle.

### Instrumentation de Station Météo (LabVIEW)
Développement d'une application d'acquisition et de traitement de données pour une station météo multi-capteurs.
* Acquisition en temps réel des données de capteurs de température, d'humidité et de vent.
* Traitement des signaux à l'aide de la bibliothèque NI-DAQmx pour la détection de pics et le filtrage des données.

## Compétences Techniques

* **Langages de programmation :** C, C++, Python, Java, SQL, LabVIEW
* **Systèmes et OS :** Linux Embarqué (BeagleBone), Systèmes d'Exploitation Temps Réel (RTOS)
* **Matériel et CAO :** MSP430, STM32F4, Arduino, KiCad
* **Outils de développement :** Git, GitHub, VS Code, MATLAB, Simulink, VirtualBox

## A propos du code
Ces projets font partie de mon parcours académique. Les ressources partagées ici se concentrent sur le prototypage fonctionnel et la logique algorithmique plutôt que sur une optimisation prête pour la production.

## Contact

* **Email :** emmanuelgautho@gmail.com
* **LinkedIn :**


# Embedded Systems and Robotics Portfolio

This repository serves as a technical portfolio highlighting my engineering projects. I am Emmanuel Gautho, currently a second-year engineering student at ESIGELEC specializing in Embedded Systems. My work focuses on mobile robotics, embedded firmware development, and computer vision.

## Projects

### Quadruped Robot Navigation (Deep Robotics Lite3 & ROS2)
Developed a perception and autonomous navigation stack for a quadruped robot to handle complex environments.
* Designed and implemented a stair-detection system using an Intel RealSense camera combined with YOLO and OpenCV.
* Processed real-time video and depth data streams to extract environment features.
* Created custom ROS2 nodes to interface the vision data with the robot's motion control system.

### Autonomous Mobile Robot (MSP430)
Designed the bare-metal firmware for a small autonomous vehicle focused on obstacle avoidance and path tracking.
* Interfaced and processed signals from ultrasonic distance sensors.
* Managed actuators and DC motors using PWM signals and hardware interrupts.
* Optimized low-level C code to operate efficiently within limited hardware resources on a Texas Instruments MSP430G2553 microcontroller.

### Electronic Design and PCB Routing (KiCad)
Completed the hardware design for an embedded system integrating a microcontroller and various sensors.
* Developed the full schematic diagram and mapped corresponding footprints.
* Routed the PCB tracks while ensuring signal integrity and proper power distribution.
* Generated Gerber files ready for industrial manufacturing.

### Weather Station Instrumentation (LabVIEW)
Built a data acquisition and processing application for a multi-sensor weather station.
* Acquired real-time data from temperature, humidity, and wind sensors.
* Processed signals using the NI-DAQmx library for peak detection and data filtering.

## Technical Skills

* **Programming Languages:** C, C++, Python, Java, SQL, LabVIEW
* **Systems and OS:** Embedded Linux (BeagleBone), Real-Time Operating Systems (RTOS)
* **Hardware and EDA:** MSP430, STM32F4, Arduino, KiCad
* **Development Tools:** Git, GitHub, VS Code, MATLAB, Simulink, VirtualBox

## About the Code
These projects are part of my academic learning curve. The code resources shared here focus on functional prototyping and algorithm logic rather than production-ready optimization.

## Contact

* **Email:** emmanuelgautho@gmail.com
* **LinkedIn:** 
