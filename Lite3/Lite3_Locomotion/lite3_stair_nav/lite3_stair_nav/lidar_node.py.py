#!/usr/bin/env python3
import math
import struct
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import List, Optional, Tuple

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, Imu
from geometry_msgs.msg import Twist, Point
from std_msgs.msg import Bool, Float64MultiArray
from transfer_interfaces.msg import MotionSimpleCMD
from visualization_msgs.msg import Marker

PointXYZ = Tuple[float, float, float]

@dataclass
class StairDetectionResult:
    detected: bool
    confidence: float
    box_count: int  
    first_step_distance: float
    mean_step_height: float
    mean_step_depth: float
    x_range: Optional[Tuple[float, float]]
    details: dict

def empty_detection() -> StairDetectionResult:
    return StairDetectionResult(
        detected=False,
        confidence=0.0,
        box_count=0,
        first_step_distance=0.0,
        mean_step_height=0.0,
        mean_step_depth=0.0,
        x_range=None,
        details={},
    )

def extract_xyz_from_pointcloud2(msg: PointCloud2) -> List[PointXYZ]:
    points = []
    field_offsets = {field.name: field.offset for field in msg.fields}
    if "x" not in field_offsets or "y" not in field_offsets or "z" not in field_offsets:
        return points

    x_offset = field_offsets["x"]
    y_offset = field_offsets["y"]
    z_offset = field_offsets["z"]
    endian = ">" if msg.is_bigendian else "<"

    for i in range(0, len(msg.data), msg.point_step):
        try:
            x = struct.unpack_from(endian + "f", msg.data, i + x_offset)[0]
            y = struct.unpack_from(endian + "f", msg.data, i + y_offset)[0]
            z = struct.unpack_from(endian + "f", msg.data, i + z_offset)[0]
        except struct.error:
            continue

        if math.isfinite(x) and math.isfinite(y) and math.isfinite(z):
            points.append((x, y, z))
    return points

def filter_roi(
    points: List[PointXYZ],
    x_min: float = 1.0,
    x_max: float = 4.0,
    y_abs_max: float = 5.0,
    z_min: float = -0.5,
    z_max: float = 2.5,
) -> List[PointXYZ]:
    return [
        (x, y, z)
        for x, y, z in points
        if x_min < x < x_max and abs(y) < y_abs_max and z_min < z < z_max
    ]

def extract_points_in_x_range(points: List[PointXYZ], x_range: Tuple[float, float]) -> List[PointXYZ]:
    x_min, x_max = x_range
    return [(x, y, z) for x, y, z in points if x_min <= x <= x_max]


class LidarClimberNode(Node):
    def __init__(self):
        super().__init__("stair_climber_complete")

        # ──────────────────────────────────────────────────────────────────────
        # PARAMÈTRES ET CONFIGURATION
        # ──────────────────────────────────────────────────────────────────────
        self.frame_id = str(self.declare_parameter("frame_id", "rslidar").value)
        self.input_topic = str(self.declare_parameter("input_topic", "/rslidar_points").value)
        self.measurement_topic = str(self.declare_parameter("measurement_topic", "/stair_detection_robot/measurements").value)
        
        self.ground_clearance_m = float(self.declare_parameter("ground_clearance_m", 0.06).value)
        self.ground_percentile = float(self.declare_parameter("ground_percentile", 0.08).value)
        self.averaging_window_size = int(self.declare_parameter("averaging_window_size", 10).value)
        
        # Sécurité temporelle Watchdog (Recherche)
        self.max_search_time = 8.0  
        self.start_node_time = self.get_clock().now()
        self.securite_declenchee = False

        # Constantes physiques d'expérimentation du robot
        self.PITCH_CABRAGE = -25000  # Valeur négative hors deadzone pour lever le châssis
        
        # Historiques pour l'analyse de forme
        self.mean_height_history = deque(maxlen=self.averaging_window_size)
        self.mean_depth_history = deque(maxlen=self.averaging_window_size)

        # Machine à états unifiée
        self.state = "SEARCHING_VISION"
        self.current_pitch_deg = 0.0
        self.climb_start_time = None
        self.flat_ground_counter = 0
        self.state_timer_counter = 0

        # ──────────────────────────────────────────────────────────────────────
        # COMMUNICATIONS ROS2
        # ──────────────────────────────────────────────────────────────────────
        # Publishers
        self.simple_cmd_pub = self.create_publisher(MotionSimpleCMD, 'simple_cmd', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.detected_publisher = self.create_publisher(Bool, "/stair_detection_robot/detected", 10)
        self.measurement_publisher = self.create_publisher(Float64MultiArray, self.measurement_topic, 10)
        
        # Publishers RViz Markers
        self.text_marker_publisher = self.create_publisher(Marker, "/stair_detection_robot/text_marker", 10)
        self.zone_marker_publisher = self.create_publisher(Marker, "/stair_detection_robot/zone_marker", 10)
        self.points_marker_publisher = self.create_publisher(Marker, "/stair_detection_robot/points_marker", 10)
        self.geometry_marker_publisher = self.create_publisher(Marker, "/stair_detection_robot/geometry_marker", 10)
        self.calculation_marker_publisher = self.create_publisher(Marker, "/stair_detection_robot/calculation_zone_marker", 10)

        # Subscriptions
        self.cloud_sub = self.create_subscription(PointCloud2, self.input_topic, self.pointcloud_callback, 10)
        self.imu_sub = self.create_subscription(Imu, '/imu/data', self.imu_callback, 10)

        # Timer principal de boucle de contrôle à 25Hz (0.04s)
        self.control_timer = self.create_timer(0.04, self.control_loop)

        self.get_logger().info(f"Nœud complet initialisé. Recherche d'escalier active (Timeout max: {self.max_search_time}s).")

    # ──────────────────────────────────────────────────────────────────────
    # CALLBACKS CAPTEURS
    # ──────────────────────────────────────────────────────────────────────
    def imu_callback(self, msg):
        q = msg.orientation
        sinp = 2 * (q.w * q.y - q.z * q.x)
        if abs(sinp) >= 1:
            pitch_rad = math.copysign(math.pi / 2, sinp)
        else:
            pitch_rad = math.asin(sinp)
        self.current_pitch_deg = math.degrees(pitch_rad)

    def pointcloud_callback(self, msg: PointCloud2):
        if self.state != "SEARCHING_VISION" or self.securite_declenchee:
            return

        start_time = time.perf_counter()
        points = extract_xyz_from_pointcloud2(msg)
        roi_points = filter_roi(points)

        if len(roi_points) < 40:
            result = empty_detection()
            result.details["reason"] = "Pas assez de points dans la ROI"
            self.publish_result(result, roi_points, [])
            return

        ground_z = self.estimate_ground_level(roi_points)
        stair_candidate_points = self.remove_ground_points(roi_points, ground_z)

        if len(stair_candidate_points) < 30:
            result = empty_detection()
            result.details["reason"] = "Pas assez de points hors sol"
            result.details["ground_z"] = ground_z
            self.publish_result(result, roi_points, stair_candidate_points)
            return

        raw_profile = self.build_xz_profile(stair_candidate_points)
        profile = self.smooth_profile(raw_profile)
        result = self.detect_stairs_from_plateaus(profile, ground_z)
        result = self.apply_stable_mean(result)

        processing_time_ms = (time.perf_counter() - start_time) * 1000.0
        result.details["processing_time_ms"] = processing_time_ms
        result.details["points_total"] = len(points)
        result.details["points_roi"] = len(roi_points)
        result.details["points_without_ground"] = len(stair_candidate_points)
        result.details["ground_z"] = ground_z
        result.details["ground_clearance_m"] = self.ground_clearance_m
        result.details["profile_bins"] = len(profile)

        self.publish_result(result, roi_points, stair_candidate_points)

        if result.detected and result.box_count >= 1:
            self.get_logger().warn(f"🎯 ESCALIER DETECTE par la vision ({result.box_count} montées). Lancement de la séquence H-Step.")
            self.state = "INIT_HSTEP"

    # ──────────────────────────────────────────────────────────────────────
    # TRAITEMENT DES POINTS (VISION)
    # ──────────────────────────────────────────────────────────────────────
    def estimate_ground_level(self, points):
        if len(points) == 0: return 0.0
        z_values = sorted(point[2] for point in points)
        percentile = max(0.0, min(1.0, self.ground_percentile))
        index = int(percentile * (len(z_values) - 1))
        return z_values[index]

    def remove_ground_points(self, points, ground_z):
        min_z = ground_z + self.ground_clearance_m
        return [point for point in points if point[2] > min_z]

    def build_xz_profile(self, points, bin_size=0.08):
        bins = defaultdict(list)
        for x, y, z in points:
            bin_index = int(x / bin_size)
            bins[bin_index].append(z)

        profile = []
        for bin_index in sorted(bins.keys()):
            z_values = sorted(bins[bin_index])
            if len(z_values) < 4: continue
            percentile_index = int(0.82 * (len(z_values) - 1))
            z_level = z_values[percentile_index]
            x_center = (bin_index + 0.5) * bin_size
            profile.append((x_center, z_level))
        return profile

    def smooth_profile(self, profile, window_size=3):
        if len(profile) < window_size: return profile
        smoothed = []
        half = window_size // 2
        for i in range(len(profile)):
            start = max(0, i - half)
            end = min(len(profile), i + half + 1)
            xs = [profile[j][0] for j in range(start, end)]
            zs = [profile[j][1] for j in range(start, end)]
            smoothed.append((sum(xs) / len(xs), sum(zs) / len(zs)))
        return smoothed

    def detect_stairs_from_plateaus(self, profile, ground_z):
        if len(profile) < 4:
            result = empty_detection()
            result.details["reason"] = "Profil trop court"
            return result

        plateaus = self.extract_plateaus(profile)
        plateaus = self.remove_ground_related_plateaus(plateaus, ground_z)

        if len(plateaus) < 2:
            result = empty_detection()
            result.details["plateaus"] = plateaus
            result.details["reason"] = "Pas assez de plateaux hors sol"
            return result

        rises = []
        step_heights = []
        step_depths = []
        min_step_height, max_step_height = 0.05, 0.35
        min_step_depth, max_step_depth = 0.10, 1.00

        for i in range(1, len(plateaus)):
            previous = plateaus[i - 1]
            current = plateaus[i]
            dz = current["z_mean"] - previous["z_mean"]
            dx = current["x_center"] - previous["x_center"]

            if min_step_height <= dz <= max_step_height:
                rises.append({
                    "x": current["x_start"], "z_low": previous["z_mean"],
                    "z_high": current["z_mean"], "dz": dz, "dx": dx,
                })
                step_heights.append(dz)
                if min_step_depth <= dx <= max_step_depth:
                    step_depths.append(dx)

        rise_count = len(rises)
        detected = rise_count >= 1

        if not detected:
            result = empty_detection()
            result.box_count = rise_count
            result.details["plateaus"] = plateaus
            result.details["rises"] = rises
            result.details["reason"] = "Aucune montee coherente hors sol"
            return result

        x_min = min(rise["x"] for rise in rises) - 0.20
        x_max = max(rise["x"] for rise in rises) + 0.35
        mean_step_height = sum(step_heights) / len(step_heights)
        mean_step_depth = sum(step_depths) / len(step_depths) if step_depths else 0.0
        
        confidence = min(1.0, rise_count / 3.0) * (1.0 if step_depths else 0.55) * min(1.0, len(plateaus) / 4.0)

        return StairDetectionResult(
            detected=True, confidence=confidence, box_count=rise_count,
            first_step_distance=min(rise["x"] for rise in rises),
            mean_step_height=mean_step_height, mean_step_depth=mean_step_depth,
            x_range=(x_min, x_max),
            details={
                "plateaus": plateaus, "rises": rises,
                "mean_step_height_raw": mean_step_height, "mean_step_depth_raw": mean_step_depth,
                "slope_angle_deg": self.compute_slope_angle(mean_step_height, mean_step_depth), "reason": "OK",
            },
        )

    def remove_ground_related_plateaus(self, plateaus, ground_z):
        min_z = ground_z + self.ground_clearance_m
        return [plateau for plateau in plateaus if plateau["z_mean"] > min_z]

    def extract_plateaus(self, profile):
        plateau_tolerance = 0.055
        min_bins_per_plateau = 2
        plateaus = []
        current_points = [profile[0]]
        current_mean_z = profile[0][1]

        for i in range(1, len(profile)):
            x, z = profile[i]
            if abs(z - current_mean_z) <= plateau_tolerance:
                current_points.append((x, z))
                current_mean_z = sum(point[1] for point in current_points) / len(current_points)
            else:
                plateau = self.make_plateau(current_points)
                if plateau is not None and plateau["bin_count"] >= min_bins_per_plateau:
                    plateaus.append(plateau)
                current_points = [(x, z)]
                current_mean_z = z

        plateau = self.make_plateau(current_points)
        if plateau is not None and plateau["bin_count"] >= min_bins_per_plateau:
            plateaus.append(plateau)
        return self.merge_close_plateaus(plateaus)

    def make_plateau(self, points):
        if len(points) == 0: return None
        xs = [point[0] for point in points]
        zs = [point[1] for point in points]
        return {
            "x_start": min(xs), "x_end": max(xs), "x_center": sum(xs) / len(xs),
            "z_mean": sum(zs) / len(zs), "depth": max(xs) - min(xs), "bin_count": len(points),
        }

    def merge_close_plateaus(self, plateaus):
        if len(plateaus) <= 1: return plateaus
        merged = []
        current = plateaus[0]
        z_merge_tolerance, x_gap_tolerance = 0.045, 0.16

        for i in range(1, len(plateaus)):
            candidate = plateaus[i]
            z_close = abs(candidate["z_mean"] - current["z_mean"]) < z_merge_tolerance
            x_close = candidate["x_start"] - current["x_end"] < x_gap_tolerance

            if z_close and x_close:
                total_bins = current["bin_count"] + candidate["bin_count"]
                current = {
                    "x_start": current["x_start"], "x_end": candidate["x_end"],
                    "x_center": (current["x_center"] * current["bin_count"] + candidate["x_center"] * candidate["bin_count"]) / total_bins,
                    "z_mean": (current["z_mean"] * current["bin_count"] + candidate["z_mean"] * candidate["bin_count"]) / total_bins,
                    "depth": candidate["x_end"] - current["x_start"], "bin_count": total_bins,
                }
            else:
                merged.append(current)
                current = candidate
        merged.append(current)
        return merged

    def apply_stable_mean(self, result):
        if not result.detected: return result
        if result.mean_step_height > 0.0: self.mean_height_history.append(result.mean_step_height)
        if result.mean_step_depth > 0.0: self.mean_depth_history.append(result.mean_step_depth)

        if len(self.mean_height_history) > 0:
            result.mean_step_height = sum(self.mean_height_history) / len(self.mean_height_history)
        if len(self.mean_depth_history) > 0:
            result.mean_step_depth = sum(self.mean_depth_history) / len(self.mean_depth_history)

        result.details["mean_step_height_stable"] = result.mean_step_height
        result.details["mean_step_depth_stable"] = result.mean_step_depth
        result.details["slope_angle_deg"] = self.compute_slope_angle(result.mean_step_height, result.mean_step_depth)
        return result

    def compute_slope_angle(self, mean_step_height, mean_step_depth):
        if mean_step_height > 0.0 and mean_step_depth > 0.0:
            return math.degrees(math.atan(mean_step_height / mean_step_depth))
        return 0.0

    # ──────────────────────────────────────────────────────────────────────
    # BOUCLE DE CONTRÔLE ET MACHINE À ÉTATS CINÉMATIQUE
    # ──────────────────────────────────────────────────────────────────────
    def control_loop(self):
        vel = Twist()
        vel.linear.x = 0.0; vel.linear.y = 0.0; vel.linear.z = 0.0
        vel.angular.x = 0.0; vel.angular.y = 0.0; vel.angular.z = 0.0

        if self.state == "SEARCHING_VISION":
            temps_ecoule = (self.get_clock().now() - self.start_node_time).nanoseconds / 1e9
            if temps_ecoule >= self.max_search_time:
                self.get_logger().error(f"🚨 WATCHDOG TIMEOUT ({self.max_search_time}s) ! Escalier non repéré. Arrêt immédiat.")
                self.state = "STOP_TIMEOUT"
                self.securite_declenchee = True
                self.cmd_vel_pub.publish(vel)
                return

        if self.state == "SEARCHING_VISION":
            vel.linear.x = 0.15  
            self.cmd_vel_pub.publish(vel)

        elif self.state == "INIT_HSTEP":
            self.get_logger().info('Étape 1 : Envoi de la commande High Step (0x21010407)')
            hstep = MotionSimpleCMD()
            hstep.cmd_code = 0x21010407
            hstep.size = 0; hstep.type = 0
            self.simple_cmd_pub.publish(hstep)
            
            self.state = "WAIT_FOR_GAIT"
            self.state_timer_counter = 0

        elif self.state == "WAIT_FOR_GAIT":
            self.state_timer_counter += 1
            if self.state_timer_counter >= 50: 
                self.state = "SET_PITCH"

        elif self.state == "SET_PITCH":
            self.get_logger().info(f'Étape 2 : Cabrage du châssis - Pitch cible : {self.PITCH_CABRAGE} (0x21010130)')
            pitch_cmd = MotionSimpleCMD()
            pitch_cmd.cmd_code = 0x21010130
            pitch_cmd.size = self.PITCH_CABRAGE
            pitch_cmd.type = 0
            self.simple_cmd_pub.publish(pitch_cmd)
            
            self.state = "WAIT_FOR_PITCH"
            self.state_timer_counter = 0

        elif self.state == "WAIT_FOR_PITCH":
            self.state_timer_counter += 1
            if self.state_timer_counter >= 25: 
                self.get_logger().info('Étape 3 : Début de l ascension active à 0.27 m/s')
                self.climb_start_time = self.get_clock().now().seconds_nanoseconds()[0]
                self.state = "CLIMBING"

        elif self.state == "CLIMBING":
            current_time = self.get_clock().now().seconds_nanoseconds()[0]
            elapsed = current_time - self.climb_start_time
            
            is_flat = abs(self.current_pitch_deg) < 5.0
            
            if elapsed > 40.0:
                self.get_logger().warn('Fin de séquence : Temps limite de montée dépassé (40s). Arrêt par sécurité.')
                self.stop_and_reset()
            
            elif elapsed > 15.0 and is_flat:
                self.flat_ground_counter += 1
                if self.flat_ground_counter > 15: 
                    self.get_logger().info('🏁 Fin de séquence : Haut de l escalier détecté avec succès par l IMU.')
                    self.stop_and_reset()
            else:
                self.flat_ground_counter = 0
                vel.linear.x = 0.27
                self.cmd_vel_pub.publish(vel)

        elif self.state in ["STOP_TIMEOUT", "FINISHED"]:
            self.cmd_vel_pub.publish(vel)

    def stop_and_reset(self):
        self.state = "FINISHED"
        self.cmd_vel_pub.publish(Twist())
        
        self.get_logger().info('Réinitialisation : Désactivation du H-Step vers mode plat standard.')
        reset_gait = MotionSimpleCMD()
        reset_gait.cmd_code = 0x21010300
        reset_gait.size = 0; reset_gait.type = 0
        self.simple_cmd_pub.publish(reset_gait)
        
        reset_pitch = MotionSimpleCMD()
        reset_pitch.cmd_code = 0x21010130
        reset_pitch.size = 0; reset_pitch.type = 0
        self.simple_cmd_pub.publish(reset_pitch)
        
        self.get_logger().info('Robot stabilisé sur le palier haut. Arrêt du timer de contrôle.')
        self.control_timer.cancel()

    # ──────────────────────────────────────────────────────────────────────
    # PUBLICATION DES MESSAGES DE DIAGNOSTIC ET RVIZ MARKERS
    # ──────────────────────────────────────────────────────────────────────
    def publish_result(self, result, roi_points, stair_candidate_points):
        stamp = self.get_clock().now().to_msg()
        
        msg_bool = Bool()
        msg_bool.data = result.detected
        self.detected_publisher.publish(msg_bool)
        
        measurement_msg = Float64MultiArray()
        measurement_msg.data = [
            float(result.mean_step_depth),
            float(result.mean_step_height),
            float(result.first_step_distance),
        ]
        self.measurement_publisher.publish(measurement_msg)

        text_marker = Marker()
        text_marker.header.frame_id = self.frame_id
        text_marker.header.stamp = stamp
        text_marker.ns = "stair_detection_robot_text"
        text_marker.id = 0
        text_marker.type = Marker.TEXT_VIEW_FACING
        text_marker.action = Marker.ADD
        text_marker.pose.position.x = 1.0; text_marker.pose.position.y = 0.0; text_marker.pose.position.z = 1.1
        text_marker.pose.orientation.w = 1.0
        text_marker.scale.z = 0.17
        text_marker.color.a = 1.0
        if result.detected:
            text_marker.color.r = 0.0; text_marker.color.g = 1.0; text_marker.color.b = 0.0
            text_marker.text = (
                "ESCALIER DETECTE\n"
                f"Confiance: {result.confidence:.2f}\n"
                f"Montees: {result.box_count}\n"
                f"Hauteur moy.: {result.mean_step_height:.2f} m\n"
                f"Giron moy.: {result.mean_step_depth:.2f} m\n"
                f"1ere marche: {result.first_step_distance:.2f} m"
            )
        else:
            text_marker.color.r = 1.0; text_marker.color.g = 0.0; text_marker.color.b = 0.0
            text_marker.text = f"PAS D ESCALIER\nConfiance: {result.confidence:.2f}\nMontees: {result.box_count}"
        self.text_marker_publisher.publish(text_marker)

        if result.detected and result.x_range is not None:
            display_points = extract_points_in_x_range(stair_candidate_points, result.x_range)
            
            if display_points:
                xs, ys, zs = [p[0] for p in display_points], [p[1] for p in display_points], [p[2] for p in display_points]
                cube = Marker()
                cube.header.frame_id = self.frame_id; cube.header.stamp = stamp
                cube.ns = "stair_detection_robot_zone"; cube.id = 1
                cube.type = Marker.CUBE; cube.action = Marker.ADD
                cube.pose.position.x = (min(xs) + max(xs)) / 2.0
                cube.pose.position.y = (min(ys) + max(ys)) / 2.0
                cube.pose.position.z = (min(zs) + max(zs)) / 2.0
                cube.pose.orientation.w = 1.0
                cube.scale.x = max(max(xs) - min(xs), 0.05)
                cube.scale.y = max(max(ys) - min(ys), 0.05)
                cube.scale.z = max(max(zs) - min(zs), 0.05)
                cube.color.r = 0.0; cube.color.g = 1.0; cube.color.b = 0.0; cube.color.a = 0.25
                self.zone_marker_publisher.publish(cube)

            self.publish_sampled_points(display_points, stamp)
            self.publish_geometry_lines(result, stamp)
        else:
            self.clear_all_markers(stamp)

    def publish_sampled_points(self, points, stamp):
        if not points: return
        for pid, pub, color in [(2, self.points_marker_publisher, (1.0, 0.5, 0.0, 0.035)), 
                                (3, self.calculation_marker_publisher, (0.0, 0.75, 1.0, 0.055))]:
            m = Marker()
            m.header.frame_id = self.frame_id; m.header.stamp = stamp
            m.ns = "stair_detection_robot_points" if pid==2 else "stair_detection_robot_calculation_zone"
            m.id = pid; m.type = Marker.POINTS; m.action = Marker.ADD
            m.scale.x = m.scale.y = color[3]
            m.color.r, m.color.g, m.color.b, m.color.a = color[0], color[1], color[2], 1.0
            
            step = max(1, len(points) // (2000 if pid==2 else 3000))
            for x, y, z in points[::step]:
                p = Point()
                p.x, p.y, p.z = float(x), float(y), float(z)
                m.points.append(p)
            pub.publish(m)

    def publish_geometry_lines(self, result, stamp):
        marker = Marker()
        marker.header.frame_id = self.frame_id; marker.header.stamp = stamp
        marker.ns = "stair_detection_robot_geometry"; marker.id = 4
        marker.type = Marker.LINE_LIST; marker.action = Marker.ADD
        marker.scale.x = 0.035
        marker.color.r = 0.0; marker.color.g = 1.0; marker.color.b = 1.0; marker.color.a = 1.0

        plateaus = result.details.get("plateaus", [])
        rises = result.details.get("rises", [])
        y_line = -0.45

        for plateau in plateaus:
            p1, p2 = Point(), Point()
            p1.x, p1.y, p1.z = float(plateau["x_start"]), y_line, float(plateau["z_mean"])
            p2.x, p2.y, p2.z = float(plateau["x_end"]), y_line, float(plateau["z_mean"])
            marker.points.extend([p1, p2])

        for rise in rises:
            p1, p2 = Point(), Point()
            p1.x, p1.y, p1.z = float(rise["x"]), y_line, float(rise["z_low"])
            p2.x, p2.y, p2.z = float(rise["x"]), y_line, float(rise["z_high"])
            marker.points.extend([p1, p2])
        self.geometry_marker_publisher.publish(marker)

    def clear_all_markers(self, stamp):
        for pid, pub, ns in [(1, self.zone_marker_publisher, "stair_detection_robot_zone"),
                             (2, self.points_marker_publisher, "stair_detection_robot_points"),
                             (3, self.calculation_marker_publisher, "stair_detection_robot_calculation_zone"),
                             (4, self.geometry_marker_publisher, "stair_detection_robot_geometry")]:
            m = Marker()
            m.header.frame_id = self.frame_id; m.header.stamp = stamp
            m.ns = ns; m.id = pid; m.action = Marker.DELETE
            pub.publish(m)


def main(args=None):
    rclpy.init(args=args)
    node = LidarClimberNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Interruption manuelle reçue.')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()