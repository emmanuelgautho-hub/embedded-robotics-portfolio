import pyrealsense2 as rs
import numpy as np
import cv2
import tensorflow as tf
import math

# -----------------------------
# 1. Charger le modèle Teachable (format .h5)
# -----------------------------
MODEL_PATH = "converted_keras/keras_model.h5"
LABELS_PATH = "converted_keras/labels.txt"

model = tf.keras.models.load_model(MODEL_PATH, compile=False)

with open(LABELS_PATH, "r") as f:
    labels = f.read().splitlines()

def predict(img_bgr):
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (224, 224))
    img_resized = img_resized.astype("float32") / 255.0
    img_resized = np.expand_dims(img_resized, axis=0)
    preds = model.predict(img_resized, verbose=0)[0]
    idx = np.argmax(preds)
    return labels[idx], preds[idx]


# -----------------------------
# 2. Extraction géométrique
# -----------------------------
def extract_geometry(depth_frame, depth_intrinsics):
    depth_image = np.asanyarray(depth_frame.get_data())
    h, w = depth_image.shape

    # Filtrage profondeur (median)
    depth_image = cv2.medianBlur(depth_image, 5)

    # ROI centrale
    x_min = int(w * 0.25)
    x_max = int(w * 0.75)
    y_min = int(h * 0.25)
    y_max = int(h * 0.75)

    points = []
    for v in range(y_min, y_max, 3):
        for u in range(x_min, x_max, 3):
            d = depth_image[v, u]
            if d == 0:
                continue
            d_m = d * 0.001
            X, Y, Z = rs.rs2_deproject_pixel_to_point(depth_intrinsics, [u, v], d_m)
            if 0.2 < Z < 3.0:
                points.append([X, Y, Z])

    if len(points) < 200:
        return None

    pts = np.array(points)

    # 1) Détection du sol = points les plus bas en Y
    sol = pts[pts[:,1] < np.percentile(pts[:,1], 20)]

    # 2) Détection de la première marche = points juste au-dessus du sol
    marche = pts[(pts[:,1] > np.percentile(pts[:,1], 20)) &
                 (pts[:,1] < np.percentile(pts[:,1], 40))]

    if len(sol) < 50 or len(marche) < 50:
        return None

    # Hauteur = différence moyenne en Y
    hauteur = abs(np.mean(marche[:,1]) - np.mean(sol[:,1]))

    # Giron = différence moyenne en Z
    profondeur = abs(np.mean(marche[:,2]) - np.mean(sol[:,2]))

    # Inclinaison globale = angle entre sol et marche
    vec = np.array([
        np.mean(marche[:,2]) - np.mean(sol[:,2]),
        np.mean(marche[:,1]) - np.mean(sol[:,1])
    ])
    inclinaison = math.degrees(math.atan2(abs(vec[1]), abs(vec[0])))

    # Largeur = étendue en X
    largeur = abs(np.max(marche[:,0]) - np.min(marche[:,0]))

    return {
        "inclinaison_deg": inclinaison,
        "largeur_m": largeur,
        "hauteur_m": hauteur,
        "profondeur_m": profondeur
    }

# -----------------------------
# 3. Initialiser la RealSense
# -----------------------------
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

profile = pipeline.start(config)
depth_profile = profile.get_stream(rs.stream.depth)
depth_intrinsics = depth_profile.as_video_stream_profile().get_intrinsics()

print("RealSense OK — Appuie sur ESC pour quitter.")


# -----------------------------
# 4. Boucle principale
# -----------------------------
try:
    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()

        if not color_frame or not depth_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())

        # Prédiction Teachable
        label, score = predict(color_image)

        cv2.putText(color_image, f"{label} ({score:.2f})",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2)

       
        # -----------------------------
        if "stairs" in label.lower() and score > 0.80:
            geom = extract_geometry(depth_frame, depth_intrinsics)

            if geom is not None:
                cv2.putText(color_image, "EXTRACTION OK", (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                cv2.putText(color_image,
                            f"Inclinaison: {geom['inclinaison_deg']:.1f} deg",
                            (10, 110), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 255, 255), 2)

                cv2.putText(color_image,
                            f"Largeur: {geom['largeur_m']:.2f} m",
                            (10, 140), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 255, 255), 2)

                cv2.putText(color_image,
                            f"Hauteur: {geom['hauteur_m']:.2f} m",
                            (10, 170), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 255, 255), 2)

                cv2.putText(color_image,
                            f"Profondeur: {geom['profondeur_m']:.2f} m",
                            (10, 200), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 255, 255), 2)

        else:
            cv2.putText(color_image, "EN ATTENTE DETECTION FIABLE",
                        (10, 70), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 0, 255), 2)

        cv2.imshow("Teachable + RealSense + Geometrie", color_image)

        if cv2.waitKey(1) == 27:
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()