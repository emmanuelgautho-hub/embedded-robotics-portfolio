#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import numpy as np
import cv2
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import Twist
from transfer_interfaces.msg import MotionSimpleCMD
from cv_bridge import CvBridge
import message_filters

class RgbdClimberNode(Node):
    def __init__(self):
        super().__init__('stair_climber_nav')
        
        # ──────────────────────────────────────────────────────────────────────
        # CONFIGURATION & PARAMÈTRES DE SÉCURITÉ
        # ──────────────────────────────────────────────────────────────────────
        self.max_search_time = 8.0  # <── TEMPS MAX EN SECONDES AVANT ARRÊT SI PAS DE DÉTECTION
        self.start_node_time = self.get_clock().now()
        self.securite_declenchee = False

        self.bridge = CvBridge()
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        self.fx = self.fy = self.cx = self.cy = None
        self.frame_count = 0
        
        # États : "RECHERCHE", "ACTIVATION_HSTEP", "FRANCHISSEMENT", "STOP_SECURITE"
        self.state = "RECHERCHE"
        self.hstep_start_time = None
        
        # ──────────────────────────────────────────────────────────────────────
        # COMMUNICATIONS ROS2
        # ──────────────────────────────────────────────────────────────────────
        self.simple_cmd_pub = self.create_publisher(MotionSimpleCMD, 'simple_cmd', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        
        self.info_sub = self.create_subscription(CameraInfo, '/camera/color/camera_info', self.callback_info, 10)
        self.color_sub = message_filters.Subscriber(self, Image, '/camera/color/image_raw')
        self.depth_sub = message_filters.Subscriber(self, Image, '/camera/depth/image_rect_raw')
        
        # Le slop (tolérance de synchro) est récupéré via les paramètres ROS 2
        self.declare_parameter('sync_slop', 0.1)
        sync_slop = self.get_parameter('sync_slop').as_float()

        self.ts = message_filters.ApproximateTimeSynchronizer(
            [self.color_sub, self.depth_sub], 
            queue_size=10, 
            slop=sync_slop
        )
        self.ts.registerCallback(self.callback_vision)
        
        # Boucle de contrôle à 10 Hz
        self.control_timer = self.create_timer(0.1, self.control_loop)
        
        self.get_logger().info(f"Nœud démarré. Sécurité active : max {self.max_search_time}s (Slop synchro: {sync_slop}s).")

    def callback_info(self, msg):
        if self.fx is None:
            self.fx, self.fy = msg.k[0], msg.k[4]
            self.cx, self.cy = msg.k[2], msg.k[5]

    def pixel_to_3d(self, px, py, depth_m):
        if self.fx is None or self.fx == 0 or depth_m <= 0: 
            return np.array([0, 0, 0])
        x = (px - self.cx) * depth_m / self.fx
        y = (py - self.cy) * depth_m / self.fy
        return np.array([x, y, depth_m])

    def extraire_niveaux(self, lines, depth_img, h, w):
        roi_top, roi_bottom = int(h * 0.25), int(h * 0.90)
        candidats = []
        if lines is None: return candidats
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y1 - y2) > 12: continue
            longueur = abs(x2 - x1)
            if longueur < 50: continue
            y_moy = (y1 + y2) // 2
            if not (roi_top <= y_moy <= roi_bottom): continue
            
            mid_x, mid_y = (x1 + x2) // 2, y_moy
            if mid_y >= depth_img.shape[0] or mid_x >= depth_img.shape[1]: continue
            
            # OPTIMISATION SÉCURITÉ : Moyenne locale 3x3 pour éviter d'échantillonner un pixel mort (0)
            x_min, x_max = max(0, mid_x-1), min(w, mid_x+2)
            y_min, y_max = max(0, mid_y-1), min(h, mid_y+2)
            zone_profondeur = depth_img[y_min:y_max, x_min:x_max]
            valides = zone_profondeur[zone_profondeur > 0]
            
            if len(valides) == 0: continue # Ignorer si toute la zone est invalide
            d_mm = np.median(valides)
            dist = d_mm * 0.001
            
            if 0.40 < dist < 2.50:
                candidats.append({
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2, "y_moy": y_moy,
                    "mid_x": mid_x, "mid_y": mid_y, "depth_m": dist,
                    "point3d": self.pixel_to_3d(mid_x, mid_y, dist), "longueur": longueur
                })
                
        candidats.sort(key=lambda c: c["y_moy"])
        groupes = []
        for c in candidats:
            merge = False
            for g in groupes:
                if abs(g["y_moy"] - c["y_moy"]) < 35:
                    if c["longueur"] > g["longueur"]: g.update(c)
                    merge = True
                    break
            if not merge: groupes.append(dict(c))
        return groupes

    def calculer_metriques(self, niveaux):
        if len(niveaux) < 2:
            return 0, []
        marches = []
        for i in range(len(niveaux) - 1):
            p_bas, p_haut = niveaux[i]["point3d"], niveaux[i+1]["point3d"]

            # Sécurité contre les points 3D corrompus à (0,0,0)
            if np.all(p_bas == 0) or np.all(p_haut == 0):
                continue

            h_cm = abs(p_haut[1] - p_bas[1]) * 100
            p_cm = abs(p_haut[2] - p_bas[2]) * 100

            valide = (10.0 <= h_cm <= 25.0 and 5.0 <= p_cm <= 80.0)

            marches.append({
                "index": i+1,
                "hauteur_cm": round(h_cm, 1),
                "profondeur_cm": round(p_cm, 1),
                "dist_cam_m": round(niveaux[i]["depth_m"], 2),
                "valide": valide
            })
        return sum(1 for m in marches if m["valide"]), marches

    def callback_vision(self, color_msg, depth_msg):
        if self.fx is None or self.securite_declenchee: 
            return

        self.frame_count += 1
        frame = self.bridge.imgmsg_to_cv2(color_msg, "bgr8")
        depth_raw = self.bridge.imgmsg_to_cv2(depth_msg, "16UC1")
        h, w = frame.shape[:2]

        if depth_raw.shape[0] != h or depth_raw.shape[1] != w:
            depth_img = cv2.resize(depth_raw, (w, h), interpolation=cv2.INTER_NEAREST)
        else:
            depth_img = depth_raw

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = self.clahe.apply(gray)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 60, 160)

        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 45, minLineLength=55, maxLineGap=35)
        niveaux = self.extraire_niveaux(lines, depth_img, h, w)
        nb_valides, _ = self.calculer_metriques(niveaux)

        if self.state == "RECHERCHE" and nb_valides >= 2:
            self.get_logger().warn(f"ESCALIER DÉTECTÉ ({nb_valides} marches). Activation H-Step.")
            self.state = "ACTIVATION_HSTEP"
            self.hstep_start_time = self.get_clock().now()
            
            hstep = MotionSimpleCMD()
            hstep.cmd_code = 0x21010407
            hstep.size = 0
            hstep.type = 0
            self.simple_cmd_pub.publish(hstep)

        # Affichage Debug Image
        debug_frame = frame.copy()
        couleur = (0, 255, 0) if (nb_valides >= 2) else (0, 100, 255)
        cv2.rectangle(debug_frame, (10, 10), (450, 60), (0, 0, 0), -1)
        cv2.putText(debug_frame, f"Marches: {nb_valides} | Etat: {self.state}", 
                    (18, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, couleur, 2)
        cv2.imshow("Lite3 - Vision Watchdog", debug_frame)
        cv2.waitKey(1)

    def control_loop(self):
        vel = Twist()
        vel.linear.x = 0.0; vel.linear.y = 0.0; vel.linear.z = 0.0
        vel.angular.x = 0.0; vel.angular.y = 0.0; vel.angular.z = 0.0

        # ── SÉCURITÉ TEMPORELLE (WATCHDOG) ──
        if self.state == "RECHERCHE":
            temps_ecoule = (self.get_clock().now() - self.start_node_time).nanoseconds / 1e9
            
            if temps_ecoule >= self.max_search_time:
                self.get_logger().error(f"🚨 TIMEOUT ({self.max_search_time}s) ! Escalier non détecté. Arrêt immédiat.")
                self.state = "STOP_SECURITE"
                self.securite_declenchee = True
                self.cmd_vel_pub.publish(vel)
                return

        # ── EXÉCUTION DES ÉTATS ──
        if self.state == "RECHERCHE":
            vel.linear.x = 0.15 
            self.cmd_vel_pub.publish(vel)

        elif self.state == "STOP_SECURITE":
            vel.linear.x = 0.0 
            self.cmd_vel_pub.publish(vel)

        elif self.state == "ACTIVATION_HSTEP":
            vel.linear.x = 0.0
            self.cmd_vel_pub.publish(vel)
            elapsed = (self.get_clock().now() - self.hstep_start_time).nanoseconds / 1e9
            if elapsed >= 2.0:
                self.state = "FRANCHISSEMENT"

        elif self.state == "FRANCHISSEMENT":
            vel.linear.x = 0.25 
            self.cmd_vel_pub.publish(vel)

def main(args=None):
    rclpy.init(args=args)
    node = RgbdClimberNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Interruption manuelle reçue.")
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()