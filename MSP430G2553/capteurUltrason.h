/**
 * @file detection_obstacle.h
 * @brief Module de gestion du capteur ultrason SRF05 pour MSP430G2553.
 * @author GAUTHO Emmanuel, NJEUMEN MBIANDA Emilie 
 * @version 1.1
 * @date 2026
 */

#ifndef DETECTION_OBSTACLE_H_
#define DETECTION_OBSTACLE_H_

/* --- Constantes et Definitions --- */

/** @brief Seuil de detection d'un obstacle en centimetres. */
#define SEUIL_OBSTACLE 20

/** @brief Valeur de retour lorsqu'un obstacle est present. */
#define OBSTACLE_DETECTE 1

/** @brief Valeur de retour lorsque la voie est libre. */
#define CHEMIN_LIBRE 0


/* --- Variables Globales (Externes) --- */

/** * @brief Distance calculee en centimetres (mise a jour par l'ISR du Timer). 
 * La mention 'volatile' est cruciale car la variable change au sein d'une interruption.
 */
extern volatile unsigned int distance_cm;


/* --- Fonctions de l'API --- */

/**
 * @brief Initialise les broches Trigger et Echo, ainsi que le Timer_A pour la capture.
 * Configure la broche Trigger en sortie et la broche Echo en entree de capture.
 */
void initialiser_detection(void);

/**
 * @brief Envoie l'impulsion de declenchement (Trigger) de 10 microsecondes.
 * Cette fonction genere le signal carre physique pour lancer le cycle du capteur.
 */
void lancer_mesure(void);

/**
 * @brief Evalue la derniere distance mesuree pour verifier la presence d'un obstacle.
 * @return int Retourne OBSTACLE_DETECTE (1) si la distance est < SEUIL_OBSTACLE,
 * sinon CHEMIN_LIBRE (0).
 */
int verifier_chemin(void);

#endif /* DETECTION_OBSTACLE_H_ */
