/**
 * @file main.c
 * @brief Boucle principale du robot autonome.
 * @author GAUTHO Emmanuel, NJEUMEN MBIANDA Emilie
 * @version 1.1
 * @date 2026
 */

#include <msp430.h>
#include "ADC.h"
#include "ligne.h"
#include "robot_deplacement.h"
#include "detection_obstacle.h" 

// --- Paramètres de vitesse nominale ---
#define VITESSE_GAUCHE      4185
#define VITESSE_DROITE      4500
#define PERIOD              10000

/**
 * Point d'entrée principal de l'application.
 * Gère l'ordonnancement des tâches en temps réel (scrutation/polling).
 */
void main(void) 
{
    // Arrêt du Watchdog Timer
    WDTCTL = WDTPW | WDTHOLD;

    // --- Phase d'initialisation des modules ---
    initialiser_moteurs();     // Configuration de la PWM (Timer A1)
    initialiser_detection();   // Configuration de l'écho ultrason (Timer A1 Capture)
    ADC_init();                // Configuration du convertisseur analogique-numérique

    // --- Boucle de contrôle principale (Algorithme d'asservissement) ---
    while(1) 
    {
        // 1. Acquisition des données des capteurs infrarouges (Suivi de ligne)
        int gauche = lecture_Capteur_Gauche(0); // Lecture canal A0 (P1.0)
        int droit  = lecture_Capteur_Droit(1);  // Lecture canal A1 (P1.1)

        // 2. Vérification de la présence d'un obstacle
        int obstacle = verifier_chemin(); 

        // 3. Gestion de la sécurité (Priorité absolue à l'évitement)
        if (obstacle == OBSTACLE_DETECTE) 
        {
            stop(); // Arrêt d'urgence des moteurs
            continue; // Force le saut au début de la boucle sans évaluer la trajectoire
        }

        // 4. Logique de navigation (Suivi du ruban adhésif au sol)
        if (droit == 0 && gauche == 0) 
        {
            // Les deux capteurs détectent le fond sombre : trajectoire rectiligne
            avancer(VITESSE_GAUCHE, VITESSE_DROITE);
        }
        else if (gauche == 0 && droit == 1) 
        {
            // Déviation vers la droite : correction de trajectoire à gauche
            tourner_gauche(VITESSE_GAUCHE, 1000);
        }
        else if (gauche == 1 && droit == 0) 
        {
            // Déviation vers la gauche : correction de trajectoire à droite
            tourner_droite(VITESSE_DROITE, 1000);
        }
        else 
        {
            // Perte de ligne ou zone de transition hors repère : sécurité active
            stop();
        }
    }
}

