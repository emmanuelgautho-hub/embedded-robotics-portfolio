import nidaqmx
from nidaqmx.constants import TerminalConfiguration as tc 
from nidaqmx.constants import LineGrouping as lg
from nidaqmx.constants import Edge
import msvcrt
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import nidaqmx
from nidaqmx.constants import TerminalConfiguration as tc
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import tkinter as tk
import datetime

class CapteurTemperature:
    def __init__(self, channel="dev15/ai6", filepath=r".\data.txt"):
        """
            cette fonction initialise la classe avec une tache et un chemin de fichiers
            entre
            str channel
            chemin de fichier filepath
            sortie=none
            """
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan(
            physical_channel=channel,
            terminal_config=tc.RSE,
        )

        try:
            self.file = open(filepath, "w")
        except IOError:
            self.file = None
            print("Open Error")

        self.liste_data = []
        self.compteur_sup = 0
        self.compteur_inf = 0
        self.SEUIL_SUP = 25
        self.SEUIL_INF = 20
        self.NB_POINTS = 200
        self.INTERVAL = 100

        # Labels Tkinter (injectés depuis la fenêtre)
        self.label_temp = None
        self.label_alert = None

    def store_chart(self, value):
        """
            cette fonction ajoute des valeurs dans la liste
            entre= data value
            sortie=none
            """
        if len(self.liste_data) >= self.NB_POINTS:
            self.liste_data.pop(0)
        self.liste_data.append(value)

    def animation(self, i):
        """
            cette fonction permet l'animation en temps réel

            entre= int i
            sortie=none
            """
        data = (self.task.read() / 0.01) - 273.15
        self.store_chart(data)

        # Mise à jour du label température
        if self.label_temp is not None:
            self.label_temp.config(text=f"Température actuelle : {data:.2f} °C")

        # Vérification des seuils et mise à jour du label alerte
        if self.label_alert is not None:
            if data > self.SEUIL_SUP:
                self.label_alert.config(text=" Seuil supérieur dépassé", fg="red")
                self.compteur_sup += 1
            elif data < self.SEUIL_INF:
                self.label_alert.config(text=" Seuil inférieur atteint", fg="blue")
                self.compteur_inf += 1
            else:
                self.label_alert.config(text="Température normale", fg="green")

        # Écriture fichier
        if self.file is not None:
            self.file.write(f"{data:.2f}\n")
            self.file.flush()

        # Mise à jour graphique
        plt.cla()
        plt.title("Température (°C)")
        plt.xlabel("Points")
        plt.xlim(0, self.NB_POINTS)
        plt.ylabel("Température")
        plt.ylim(0, 50)
        plt.plot(self.liste_data, label="Température", color="blue")

        # Ajout des lignes de seuil
        plt.axhline(self.SEUIL_SUP, color="red", linestyle="--", label="Seuil haut")
        plt.axhline(self.SEUIL_INF, color="green", linestyle="--", label="Seuil bas")
        plt.legend(loc="upper right")

    def run(self):
        """
            cette fonction lance l'animation
            entre=none
            sortie=none
        """
        fig = plt.figure("NI-Scope")
        self.anim = FuncAnimation(fig, self.animation, interval=self.INTERVAL, cache_frame_data=False)
        plt.show()

    def close(self):
        """
            cette fonction ferme l'animation
            entre=none
            sortie=none
        """
        if self.file is not None:
            self.file.close()
        self.task.close()

class CapteurCompteur:
    def __init__(self, lines="dev15/port1/line0:3", filepath=r".\data1.txt"):

        """
            cette fonction initialise la classe avec une tache et un chemin de fichiers
            entre
            str lines
            chemin de fichier filepath
            sortie=none
        """

        # Tâches NI-DAQ
        self.task_bits = nidaqmx.Task()
        self.task_bits.di_channels.add_di_chan(lines=lines, line_grouping=lg.CHAN_PER_LINE)

        self.task_byte = nidaqmx.Task()
        self.task_byte.di_channels.add_di_chan(lines=lines, line_grouping=lg.CHAN_FOR_ALL_LINES)

        # Fichier
        try:
            self.file = open(filepath, "w")
        except IOError:
            self.file = None
            print("Open Error")

        # Table de correspondance
        self.tab = [15, 14, 10, 11, 9, 8, 12, 13, 5, 4, 0, 1, 3, 2, 6, 7]

    def read_binaire(self):
        """
            cette fonction lit et retourne la valeur binaire du compteur
            entre
            none
            
            sortie= str BinStr
        """
        # Construction chaîne binaire
        BinStr = "".join(("1" if b else "0") for b in self.task_bits.read()[::-1])
        value = self.task_byte.read()
        try:
            station = self.tab.index(value)
        except ValueError:
            station = -1
        return str(BinStr)
    
    def read_value(self):
        """
            cette fonction lit et retourne la valeur lue du compteur
            entre
            none
            
            sortie= str value
        """
        # Construction chaîne binaire
        BinStr = "".join(("1" if b else "0") for b in self.task_bits.read()[::-1])
        value = self.task_byte.read()
        try:
            station = self.tab.index(value)
        except ValueError:
            station = -1
        return  str(value)

    
    def read_station(self):
        """
            cette fonction lit et retourne la valeur station du compteur
            entre
            none
            
            sortie= str station
        """
        # Construction chaîne binaire
        BinStr = "".join(("1" if b else "0") for b in self.task_bits.read()[::-1])
        value = self.task_byte.read()
        try:
            station = self.tab.index(value)
        except ValueError:
            station = -1
        return str (station)



    def run(self):
        """
            cette fonction lance l'ecriture du fichier
            entre
            none
            
            sortie= none
        """
        print("Press [Q] to stop\n")
        c = " "
        while c.upper() != "Q":
            BinStr, value, station = self.read_station()
            print(f"valeurbinaire : {BinStr}    valeurlu : {value:2d}    station : {station:2d}", end="\r")

            if self.file is not None:
                self.file.write(f"{value}\n")
                self.file.flush()

            if value == 15:
                time.sleep(0.3)

            if msvcrt.kbhit():
                c = msvcrt.getwch()

        print("\n\n")

    def close(self):
        """
            cette fonction ferme la tache
            entre
            none
            
            sortie= none
        """
        self.task_bits.close()
        self.task_byte.close()
        if self.file is not None:
            self.file.close()

class CapteurGirouette:
    def __init__(self, channel="dev15/ai3", nom="Girouette"):
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan(channel)
        self.liste_data = []
        self.nom = nom
        #liste des directions
        self.directions =["N","S","W","E","NW","NE","WS","SE"]
        #listes des tensions correspondantes
        self.va=[3.76,1.42,4.47,0.47,4.21,2.25,3.06,0.92]

         # Objets matplotlib (créés une fois)
        self.fig = None
        self.ax = None
        self.line = None
        self.anim = None  # IMPORTANT: garder référence à l'animation

    def read_value(self):
        return self.task.read()

    def store_chart(self, value):
        if len(self.liste_data) >= 200:
            self.liste_data.pop(0)
        self.liste_data.append(value)

    def _init_plot(self):
        # Crée la figure/axes/line une seule fois
        self.fig, self.ax = plt.subplots(num=self.nom)
        self.ax.set_title(self.nom)
        self.ax.set_xlabel("Samples")
        self.ax.set_xlim(0, 200)
        self.ax.set_ylabel("Tension (V)")
        self.ax.set_ylim(0, 10)
        # ligne vide à mettre à jour
        self.line, = self.ax.plot([], [], color="mediumpurple")

    def affiche_dir(self):
        """
            cette fonction affiche la direction de la girouette
            entre
            none
            
            sortie= str directions
        """
        ind=0
        distance=abs(self.va[0]-self.read_value())
        for i in range(len(self.va)):
            distance1=abs(self.va[i]-self.read_value())
            if distance1<distance:
                distance=distance1
                ind=i
        return self.directions[ind]
       


    

    def save_direction(self, direction, filename="directions.log"):
        """Enregistre uniquement la direction dans un fichier texte"""
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"{direction}\n")



    def _update(self, frame):
        value = self.read_value()
        self.store_chart(value)
        # Met à jour les données de la courbe sans effacer l'axe
        x = list(range(len(self.liste_data)))
        self.line.set_data(x, self.liste_data)
        # Ajuste si moins de 200 points
        self.ax.set_xlim(0, max(200, len(self.liste_data)))
        return self.line

    def run(self):
        if self.fig is None:
            self._init_plot()
        # Garder référence à l'animation
        self.anim = FuncAnimation(
            self.fig,
            self._update,
            interval=100,
            blit=False  # blit False pour éviter soucis avec axes qui changent
        )
        plt.show()  # bloque jusqu'à fermeture de la fenêtre

    def close(self):
        self.task.close()
        # Optionnel: fermer la figure si ouverte
        if self.fig:
            plt.close(self.fig)
            self.fig = None
            self.anim = None



class CapteurAnemometre:
    def __init__(self, filepath=r".\anemometre_data.txt"):
        # Création de la tâche compteur
        self.task = nidaqmx.Task()
        self.task.ci_channels.add_ci_count_edges_chan(
            counter="dev15/ctr0",
            edge=Edge.FALLING
        ).ci_count_edges_term = "/dev15/pfi0"
        self.task.start()

        # Fichier de sauvegarde
        try:
            self.file = open(filepath, "w")
        except IOError:
            self.file = None
            print("Erreur ouverture fichier")

        # Variables internes
        self.NB_POINTS = 200
        self.INTERVAL = 100
        self.liste_data = []

        # Labels Tkinter (injectés depuis la fenêtre)
        self.label_val = None
        self.label_vit = None

    def read_value(self):
        """Lecture compteur et remise à zéro"""
        data = int(self.task.read())
        self.task.stop()
        self.task.start()
        return data

    def store_chart(self, value):
        if len(self.liste_data) >= self.NB_POINTS:
            self.liste_data.pop(0)
        self.liste_data.append(value)

    def animation(self, i):
       
        plt.cla()
        plt.title("Anénometre (brut)")
        plt.xlabel("Points")
        plt.xlim(0, self.NB_POINTS)
        plt.ylim(0, 10)
        plt.ylabel("Vitesse")
        
        
        data = self.read_value()
        vitesse = data * 2.4  # conversion en km/h
        self.store_chart(vitesse)
        plt.plot(self.liste_data, color="blue")

        
        # Écriture fichier
        if self.file is not None:
            self.file.write(f"{data};{vitesse}")
    
    def run(self):
        fig = plt.figure("NI-Scope")
        self.anim = FuncAnimation(fig, self.animation, interval=self.INTERVAL, cache_frame_data=False)
        plt.show()
    
    def close(self):
        if self.file is not None:
            self.file.close()
        self.task.close()
        self.task.close()



class CapteurPluviometrie:
    def __init__(self, filepath=r".\pluvio_data.txt"):
        # Initialisation des tâches NI
        self.task_bits = nidaqmx.Task()
        self.task_bits.di_channels.add_di_chan(
            lines="dev15/port0/line0:7",
            line_grouping=lg.CHAN_PER_LINE
        )

        self.task_byte = nidaqmx.Task()
        self.task_byte.di_channels.add_di_chan(
            lines="dev15/port0/line0:7",
            line_grouping=lg.CHAN_FOR_ALL_LINES
        )

        # Fichier de sauvegarde
        try:
            self.file = open(filepath, "w")
        except IOError:
            self.file = None
            print("Erreur ouverture fichier")

        # Variables internes
        self.compteur = 0
        self.SEUIL_SUP = 500
        self.SEUIL_INF = 60
        self.NB_POINTS = 200
        self.INTERVAL = 100
        self.liste_data = []

        # Labels Tkinter (injectés depuis la fenêtre)
        self.label_val = None
        self.label_alert = None

    def read_value(self):
        """Lecture brute (byte)"""
        return self.task_byte.read()

    def read_bits(self):
        """Lecture des bits individuels"""
        return self.task_bits.read()

    def store_chart(self, value):
        if len(self.liste_data) >= self.NB_POINTS:
            self.liste_data.pop(0)
        self.liste_data.append(value)

    def animation(self, i):
        value = self.read_value()
        self.store_chart(value)

        # Mise à jour graphique
        plt.cla()
        plt.title("Pluviométrie (brut)")
        plt.xlabel("Points")
        plt.xlim(0, self.NB_POINTS)
        plt.ylabel("Volume brut")
        plt.ylim(0, 500)
        plt.plot(self.liste_data, color="blue")

        # Ajout des lignes de seuil
        plt.axhline(self.SEUIL_SUP, color="red", linestyle="--", label="Seuil haut")
        plt.axhline(self.SEUIL_INF, color="green", linestyle="--", label="Seuil bas")
        plt.legend(loc="upper right")

    def run(self):
        fig = plt.figure("NI-Scope")
        self.anim = FuncAnimation(fig, self.animation, interval=self.INTERVAL, cache_frame_data=False)
        plt.show()

    def close(self):
        if self.file is not None:
            self.file.close()
        self.task_bits.close()
        self.task_byte.close()

