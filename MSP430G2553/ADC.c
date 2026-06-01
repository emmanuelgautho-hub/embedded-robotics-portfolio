

#include <msp430.h>
#include "ADC.h"

/**
 * Initialise le module ADC10.
 * Configure les références de tension (VCC/GND), l'horloge de conversion (SMCLK)
 * et le mode de conversion canal par canal (mono-voie, monocoup).
 */
void ADC_init(void)
{
    // Remise à zéro initiale des registres de contrôle
    ADC10CTL0 = 0;
    ADC10CTL1 = 0;

    // Configuration du registre de contrôle 0 (ADC10CTL0) :
    // - SREF_0   : Référence de tension VCC et GND
    // - ADC10SHT_0 : Temps de maintien de l'échantillonnage à 4 cycles d'horloge
    // - REF2_5V  : Générateur de référence interne configuré à 2.5V (si activé)
    // - REFON    : Activation du générateur de référence interne
    // - ADC10ON   : Activation du module ADC10
    ADC10CTL0 = SREF_0 | ADC10SHT_0 | REF2_5V | REFON | ADC10ON;

    // Configuration du registre de contrôle 1 (ADC10CTL1) :
    // - ADC10DIV_0 : Diviseur de fréquence par 1
    // - ADC10SSEL_2 : Choix de la source d'horloge SMCLK (~1 MHz)
    // - SHS_0      : Déclenchement de la conversion par logiciel (bit ADC10SC)
    // - CONSEQ_0   : Mode de conversion unique (Single-channel, single-conversion)
    ADC10CTL1 = ADC10DIV_0 | ADC10SSEL_2 | SHS_0 | CONSEQ_0;
}

/**
 * Sélectionne un canal analogique et lance une conversion unique.
 * @param voie Index du canal analogique à mesurer (ex: 0 pour A0, 1 pour A1).
 */
void ADC_Demarrer_conversion(unsigned char voie)
{
    // Configuration du canal d'entrée en décalant l'index de la voie dans les bits INCHx
    ADC10CTL1 = (voie * 0x1000) | ADC10DIV_0 | ADC10SSEL_2 | SHS_0 | CONSEQ_0;
    
    // Activation de la conversion (ENC) et déclenchement du cycle d'échantillonnage (ADC10SC)
    ADC10CTL0 |= ENC | ADC10SC;
}  

/**
 * Attend la fin de la conversion en cours et retourne la valeur lue.
 * @return int Résultat de la conversion codé sur 10 bits (valeur entre 0 et 1023).
 */
int ADC_Lire_resultat(void)
{
    // Attente active tant que le bit ADC10BUSY est à 1 (conversion en cours)
    while (ADC10CTL1 & ADC10BUSY);
    
    // Désactivation temporaire de la conversion pour autoriser les modifications de registres
    ADC10CTL0 &= ~ENC;

    // Retourne le registre mémoire contenant le résultat de la conversion
    return ADC10MEM;
}
