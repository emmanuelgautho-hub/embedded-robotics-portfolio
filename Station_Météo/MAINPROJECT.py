import time
import tkinter as tk
from tkinter import *
from PIL import Image, ImageTk


from CAPTEURS import CapteurTemperature, CapteurAnemometre, CapteurPluviometrie, CapteurCompteur, CapteurGirouette

# ----------------- FENÊTRE -----------------
"""
cette partie concerne la configuration de la fenetre d'apparition des capteurs
"""
window = Tk()
window.title("Projet Station Météo")
window.geometry("800x900")
window.config(background="#A4ADDB")
window.resizable(False, False)

# ----------------- TITRE + LOGO -----------------
"""
cette partie  crée le logo
"""
header = Frame(window, bg="#A4ADDB")
header.grid(row=0, column=0, padx=10, pady=15)

try:
    logo_img = Image.open("Logo_ESIGELEC-removebg-preview.png") #les images doivent se trouver dans le meme dossier que le fichier
    logo_img = logo_img.resize((100,80 ))
    logo = ImageTk.PhotoImage(logo_img)
except:
    logo = None

logo_canvas = Canvas(header, width=100, height=130, bg="#A4ADDB", highlightthickness=0)
logo_canvas.grid(row=0, column=0, padx=10)
if logo:
    logo_canvas.create_image(50, 65, image=logo)

Label(header, text="STATION MÉTÉO ESIGELEC",
      font=("Courrier", 32), bg="#A4ADDB", fg="white").grid(row=0, column=1)


#------------FONCTION OUVERTURE SOUS FENETRE-----------------------------
def open_new_window(title):
    """
    cette fonction ouvre des sous fenetres personnalisés à l'appui des boutons pour chaque capteur
    entre= str title
    sortie=none
    """
    win = Toplevel(window)
    win.title(title)
    win.geometry("700x600")
    win.config(background="#A4ADDB")

    Label(win, text=title, font=("Courrier", 20),
          bg="#A4ADDB", fg="white").pack(pady=20)

    # On instancie la classe correspondant au capteur
    if title=="TEMPÉRATURE" :
        """
        permet de vérifier le bouton qui a été appuyé
        
        """
        capteur = CapteurTemperature()

        # Label température
        temp_label = Label(win, text="Température actuelle : -- °C",
                        font=("Courrier", 16), bg="#A4ADDB", fg="white")
        temp_label.pack(pady=10)

        # Label alerte
        alert_label = Label(win, text="Température normale",
                            font=("Courrier", 16), bg="#A4ADDB", fg="green")
        alert_label.pack(pady=10)
   
        result_label = Label(win, text="", font=("Courrier", 14),
                         bg="#A4ADDB", fg="yellow")
        result_label.pack(pady=10)

        # On donne les labels à la classe
        capteur.label_temp = temp_label
        capteur.label_alert = alert_label

        history = []

        running = {"on": False}
        
        def calculer_temps_hors_seuil(history, seuil_inf, seuil_sup): #implémentation du calcul du temps fait par IA
            """
            cette fonction calcul le temps hors seuil_temp
            entree:
            history doit être une liste de tuples : (timestamp, valeur)
            timestamp = time.monotonic()
            valeur = température
            sortie:
            Retourne le temps total hors seuils en secondes.
            """
            if not history:
                return 0.0

            total = 0.0
            in_period = False
            start_ts = None

            for ts, val in history:
                outside = (val < seuil_inf) or (val > seuil_sup)

                if outside and not in_period:
                    in_period = True
                    start_ts = ts

                elif not outside and in_period:
                    total += ts - start_ts
                    in_period = False
                    start_ts = None

            # Si la dernière valeur est hors seuil, on ferme la période
            if in_period and start_ts is not None:
                total += history[-1][0] - start_ts

            return total

        def update_labels(): #Solution proposée par IA suite a un probleme de boucle infinie
            """
            cette fonction met à jour la mesure des valeurs et des graphes
            entre= none
            sortie=none
            """
            if running["on"]:
                # lecture capteur
                data = (capteur.task.read() / 0.01) - 273.15
                temp_label.config(text=f"Température actuelle : {data:.2f} °C")

                history.append((time.monotonic(), data))
                # alerte seuils
                if data > capteur.SEUIL_SUP:
                    alert_label.config(text=" Seuil supérieur dépassé", fg="red")
                    capteur.compteur_sup+=1
                elif data < capteur.SEUIL_INF:
                    alert_label.config(text=" Seuil inférieur atteint", fg="blue")
                    capteur.compteur_inf+=1
                else:
                    alert_label.config(text="Température normale", fg="green")
                

                # relance après 300 ms
                win.after(300, update_labels)

        def start_read():
            """
            cette fonction lance la lecture des valeurs
            entre=none
            sortie=none
            """
            running["on"] = True
            update_labels()

        def stop_read():
            """
            cette fonction arrete la lecture des valeurs
            entre=none
            sortie=none
            """
            running["on"] = False
            capteur.close()
            temps_total = (capteur.compteur_sup + capteur.compteur_inf) * 0.3
            
            temps_total = calculer_temps_hors_seuil(
                history,
                capteur.SEUIL_INF,
                capteur.SEUIL_SUP
            )

            result_label.config(text=f"Temps hors seuils : {temps_total:.1f} secondes")
           # win.destroy()  # ferme la fenêtre

        # Boutons
        Button(win, text="Start lecture", command=start_read).pack(pady=10)
        Button(win, text="Stop lecture", command=stop_read).pack(pady=10)
        Button(win, text="Afficher Graphique", command=capteur.run).pack(pady=20)


    elif title=="COMPTEUR" :
        capteur = CapteurCompteur()

        Label(win, text="Station :").pack(pady=10)
        Sta_label = Label(win, text="--")
        Sta_label.pack(pady=10)

        Label(win, text="Valeur Lue :").pack(pady=10)
        Val_label = Label(win, text="--")
        Val_label.pack(pady=10)

        Label(win, text="Binaire :").pack(pady=10)
        Bin_label = Label(win, text="--")
        Bin_label.pack(pady=10)

        running = {"on": True}

        def update_labels():
            """
            cette fonction met à jour la mesure des valeurs et des graphes
            entre= none
            sortie=none
            """
            if running["on"]:
                # lecture capteur
                valeur = capteur.read_value()
                station = capteur.read_station()
                binaire = capteur.read_binaire()

                # mise à jour des labels
                Sta_label.config(text=station)
                Val_label.config(text=valeur)
                Bin_label.config(text=binaire)

                # relance après 500 ms
                win.after(500, update_labels)

        # bouton pour arrêter la lecture
        def stop_read():
            """
            cette fonction arrete  la lecture des valeurs
            entre=none
            sortie=none
            """
            running["on"] = False
            capteur.close()
            win.destroy()

        Button(win, text="Stop lecture", command=stop_read).pack(pady=20)

        # démarrage de la boucle
        update_labels()



    elif title=="ANÉMOMÈTRE" :
        capteur = CapteurAnemometre()
        Button(win, text="Afficher Graphique", command=capteur.run).pack(pady=20)
        
        # Label impulsions
        val_label = Label(win, text="Impulsions : --",
                          font=("Courrier", 16), bg="#A4ADDB", fg="white")
        val_label.pack(pady=10)

        # Label vitesse
        vit_label = Label(win, text="Vitesse : -- km/h",
                          font=("Courrier", 16), bg="#A4ADDB", fg="white")
        vit_label.pack(pady=10)

        # On donne les labels à la classe
        capteur.label_val = val_label
        capteur.label_vit = vit_label

        running = {"on": False}

        def update_labels():
            """
            cette fonction met à jour la mesure des valeurs et des graphes
            entre= none
            sortie=none
            """
            if running["on"]:
                data = capteur.read_value()
                vitesse = data * 2.4
                val_label.config(text=f"Impulsions : {data}")
                vit_label.config(text=f"Vitesse : {vitesse:.1f} km/h")

                # Sauvegarde fichier
                if capteur.file is not None:
                    capteur.file.write(f"{data};{vitesse:.1f}\n")
                    capteur.file.flush()

                win.after(300, update_labels)

        def start_read():
            """
            cette fonction lance  la lecture des valeurs
            entre=none
            sortie=none
            """
            running["on"] = True
            update_labels()

        def stop_read():
            """
            cette fonction arrete  la lecture des valeurs
            entre=none
            sortie=none
            """
            running["on"] = False
            capteur.close()
            win.destroy()

        # Boutons
        Button(win, text="Start lecture", command=start_read).pack(pady=10)
        Button(win, text="Stop lecture", command=stop_read).pack(pady=10)
        


    elif title=="PLUVIOMÈTRE" :
        capteur = CapteurPluviometrie()
        Button(win, text="Afficher Graphique", command=capteur.run).pack(pady=20)

    

        # Label valeur brute
        val_label = Label(win, text="Valeur brute : -- ",
                            font=("Courrier", 16), bg="#A4ADDB", fg="white")
        val_label.pack(pady=10)

        # Label compteur en ml
        ml_label = Label(win, text="Volume : -- ml",
                            font=("Courrier", 16), bg="#A4ADDB", fg="white")
        ml_label.pack(pady=10)

        # Label alerte
        alert_label = Label(win, text="Volume normal",
                            font=("Courrier", 16), bg="#A4ADDB", fg="green")
        alert_label.pack(pady=10)

        capteur.label_val = val_label
        capteur.label_alert = alert_label

        running = {"on": False}

        def update_labels():
            """
            cette fonction met à jour la mesure des valeurs et des graphes
            entre= none
            sortie=none
            """
            if running["on"]:
                value = capteur.read_value()

                # Affichage brut
                val_label.config(text=f"Valeur brute : {value}")

                # Conversion en ml
                if value == 255:
                    capteur.compteur += 5
                ml_label.config(text=f"Volume : {capteur.compteur} ml")

                # Seuils
                if capteur.compteur > capteur.SEUIL_SUP:
                    alert_label.config(text="Seuil supérieur atteint !", fg="red")
                elif capteur.compteur < capteur.SEUIL_INF:
                    alert_label.config(text="Seuil inférieur atteint !", fg="blue")
                else:
                    alert_label.config(text="Volume normal", fg="green")

                # Sauvegarde fichier
                if capteur.file is not None:
                    capteur.file.write(f"{capteur.compteur}\n")
                    capteur.file.flush()

                win.after(300, update_labels)

        def start_read():
            """
            cette fonction lance  la lecture des valeurs
            entre=none
            sortie=none
            """
            running["on"] = True
            update_labels()

        def stop_read():
            """
            cette fonction arrete  la lecture des valeurs
            entre=none
            sortie=none
            """
            running["on"] = False
            capteur.close()
            win.destroy()

        # Boutons
        Button(win, text="Start lecture", command=start_read).pack(pady=10)
        Button(win, text="Stop lecture", command=stop_read).pack(pady=10)
        


    

    elif title=="GIROUETTE" :
        capteur = CapteurGirouette()

        # Label valeur
        Val_label = Label(win, text="Valeur lue : -- ",
                        font=("Courrier", 16), bg="#A4ADDB", fg="white")
        Val_label.pack(pady=10)
        

        # Label dir
        dir_label = Label(win, text=" Directions : -- ",
                        font=("Courrier", 16), bg="#A4ADDB", fg="white")
        dir_label.pack(pady=10)
        Button(win, text="Afficher Graphique", command=capteur.run).pack(pady=20)


        running = {"on": False}

        def update_labels():
            """
            cette fonction met à jour la mesure des valeurs et des graphes
            entre= none
            sortie=none
            """
            if running["on"]:
                # lecture capteur
                data = capteur.read_value()
                Val_label.config(text=f"Valeur lue : {data:.2f} ")

                dir_label.config(text=capteur.affiche_dir()) 

                capteur.save_direction(capteur.affiche_dir())
                

                # relance après 300 ms
        
                win.after(100, update_labels)

        def start_read():
            """
            cette fonction lance la lecture des valeurs
            entre=none
            sortie=none
            """
            running["on"] = True
            update_labels()

        def stop_read():
            """
            cette fonction arrete  la lecture des valeurs
            entre=none
            sortie=none
            """
            running["on"] = False
            capteur.close()
          
            
            win.destroy()  # ferme la fenêtre

        # Boutons
        Button(win, text="Start lecture", command=start_read).pack(pady=10)
        Button(win, text="Stop lecture", command=stop_read).pack(pady=10)
        

# ----------------- FONCTION POUR BLOCS -----------------
def create_block(parent, title, img_file, size=(120, 120)):
    """
            cette fonction crée les blocks a implémenter dans l'IHM a savoir titre image bouton
            entre:
            Any parent 
            str title
            image img_file
            tuple size 
            sortie=none
            """
    frame = Frame(parent, bg="#A4ADDB")

    Label(frame, text=title, font=("Courrier", 16),
          bg="#A4ADDB", fg="white").pack(pady=5)

    try:
        img = Image.open(img_file)
        img = img.resize(size)
        img = ImageTk.PhotoImage(img)
    except:
        img = None

    canvas = Canvas(frame, width=140, height=140, bg="#A4ADDB", highlightthickness=0)
    canvas.pack()

    if img:
        canvas.create_image(70, 70, image=img)
    canvas.image = img
    Button(frame, text="Ouvrir", bg="white", fg="#A4ADDB",
        command=lambda: open_new_window(title)).pack(pady=5)

    return frame

# ----------------- GRILLE PRINCIPALE -----------------
grid = Frame(window, bg="#A4ADDB")
grid.grid(row=1, column=0, pady=10)

grid.grid_columnconfigure(0, minsize=250)
grid.grid_columnconfigure(1, minsize=250)
grid.grid_columnconfigure(2, minsize=250)

# ----------- LIGNE 0 : TEMP + ANÉMO -----------
temp = create_block(grid, "TEMPÉRATURE", "temperature.png")
anem = create_block(grid, "ANÉMOMÈTRE", "wind-power.png")

temp.grid(row=0, column=0, pady=10)
anem.grid(row=0, column=2, pady=10)

# ----------- LIGNE 1 : PLUVIO CENTRAL -----------
pluv = create_block(grid, "PLUVIOMÈTRE", "heavy-rain.png")
pluv.grid(row=1, column=1, pady=10)

# ----------- LIGNE 2 : COMPTEUR + GIROUETTE -----------
compteur = create_block(grid, "COMPTEUR", "counter.png")
gir = create_block(grid, "GIROUETTE", "forecast.png")

compteur.grid(row=2, column=0, pady=10)
gir.grid(row=2, column=2, pady=10)

# ----------------- MAINLOOP -----------------
window.mainloop()
