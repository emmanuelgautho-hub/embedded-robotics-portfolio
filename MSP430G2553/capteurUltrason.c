/**
 * @file detection_obstacle.c
 * @brief Implémentation du pilote pour le capteur ultrason SRF05.
 * @author  GAUTHO Emmanuel NJEUMEN MBIANDA Emilie 
 * @version 1.1
 * @date 2026
 */

#include <msp430.h>
#include "detection_obstacle.h"

/* --- Variables privées du module (accessibles par l'ISR) --- */
static volatile unsigned int t_montee = 0;
static volatile unsigned int t_descente = 0;

/* --- Variable globale externe --- */
volatile unsigned int distance_cm = 0;

/**
 * Configure les périphériques matériels pour le HC-SR04.
 * P1.1 -> Sortie Trigger numérique.
 * P2.1 -> Entrée Echo connectée au bloc de capture du Timer A1 (TA1.1 / CCI1A).
 */
void initialiser_detection(void) 
{
    // 1. Configuration de la broche Trigger (P1.1) en sortie standard
    P1DIR |= BIT1;
    P1OUT &= ~BIT1; // Niveau bas initial

    // 2. Configuration de la broche Echo (P2.1) en entrée de fonction alternative
    P2DIR &= ~BIT1;
    P2SEL |= BIT1;   // Redirection vers le Timer_A1 (CCI1A)

    // 3. Configuration de la base de temps du Timer A1
    // Source SMCLK (1 MHz nominal), Mode Continu (compte de 0 à 0xFFFF)
    TA1CTL = TASSEL_2 | MC_2 | TACLR;

    // 4. Configuration du bloc de capture (TA1CCTL1)
    // Mode Capture (CAP), Capture sur les deux fronts (CM_3), Entrée CCI1A (CCIS_0),
    // Capture Synchrone (SCS), Activation de l'interruption locale (CCIE)
    TA1CCTL1 = CAP | CM_3 | CCIS_0 | SCS | CCIE;

    // Activation globale des interruptions
    __enable_interrupt();
}

/**
 * Émet l'impulsion physique de déclenchement sur la broche Trigger.
 * Demande au HC-SR04 de lancer une salve de 8 impulsions ultrasonores.
 */
void lancer_mesure(void) 
{
    P1OUT |= BIT1;
    __delay_cycles(10); // Impulsion de synchronisation de 10 microsecondes
    P1OUT &= ~BIT1;
}

/**
 * Routine d'interruption (ISR) dédiée au vecteur d'interruption du Timer A1.
 * Intercepte les fronts sur la broche Echo pour mesurer la largeur temporelle.
 */
#pragma vector = TIMER1_A1_VECTOR
__interrupt void Timer_A1_ISR(void) 
{
    // Vérification de la source de l'interruption (Vecteur partagé TA1IV)
    if (TA1IV == TA1IV_TACCR1) 
    {
        if (P2IN & BIT1) 
        {
            // Front Montant : Début du signal Echo, sauvegarde du timestamp initial
            t_montee = TA1CCR1;
        } 
        else 
        {
            // Front Descendant : Fin du signal Echo, calcul du delta temps
            t_descente = TA1CCR1;
            
            // Distance (cm) = Durée de l'impulsion (µs) / 58
            distance_cm = (t_descente - t_montee) / 58;
        }
    }
}

/**
 * Envoie une requête de mesure et analyse l'environnement.
 * @return OBSTACLE_DETECTE (1) ou CHEMIN_LIBRE (0) selon le seuil matériel.
 */
int verifier_chemin(void) 
{
    lancer_mesure();
    
    // Attente de la fin du cycle d'écho (50 000 cycles d'horloge)
    __delay_cycles(50000);

    // Évaluation par rapport au seuil critique de 20 cm
    if (distance_cm > 0 && distance_cm < SEUIL_OBSTACLE) 
    {
        return OBSTACLE_DETECTE;
    }

    return CHEMIN_LIBRE;
}