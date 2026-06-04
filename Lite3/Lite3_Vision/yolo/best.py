import pyrealsense2 as rs
import numpy as np
import cv2
from ultralytics import YOLO

# -----------------------------
# Chargement du modèle YOLO
# -----------------------------
model = YOLO("best.pt")   # Ton modèle entraîné

# -----------------------------
# Initialisation RealSense
# -----------------------------
pipeline = rs.pipeline()
config = rs.config()

# Flux couleur uniquement
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

pipeline.start(config)

# -----------------------------
# Boucle principale
# -----------------------------
try:
    while True:

        # Récupération des frames
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()

        if not color_frame:
            continue

        # Conversion en tableau NumPy
        frame = np.asanyarray(color_frame.get_data())
        annotated = frame.copy()

        # -----------------------------
        #  Détection avec YOLO
        # -----------------------------
        results = model(frame)

        for r in results:
            for box in r.boxes:

                # Confiance 
                conf = float(box.conf[0])

                # Coordonnées de la bounding box
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                cls = int(box.cls[0])
                label = model.names[cls]

                # Dessin de la box
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(annotated, f"{label} {conf:.2f}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            (0, 255, 0), 2)

        # -----------------------------
        #  Affichage final
        # -----------------------------
        cv2.imshow("YOLO - Test du modèle", annotated)

        if cv2.waitKey(1) == 27:  # Touche ESC
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
