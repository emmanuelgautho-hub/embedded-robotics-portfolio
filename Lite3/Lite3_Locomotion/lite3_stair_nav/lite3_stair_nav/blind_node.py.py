#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from transfer_interfaces.msg import MotionSimpleCMD
import math

class BlindClimberNode(Node):
    def __init__(self):
        super().__init__('stair_climber_blind')
        
        # Publishers vers les topics gérés par Jetson2Motion
        self.simple_cmd_pub = self.create_publisher(MotionSimpleCMD, 'simple_cmd', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        
        # Subscriber pour l'IMU
        self.imu_sub = self.create_subscription(Imu, '/imu/data', self.imu_callback, 10)
        
        # Variables de contrôle de la machine à états
        self.current_pitch_deg = 0.0
        self.start_time = None
        self.is_climbing = False
        self.flat_ground_counter = 0
        self.state = "INIT"
        
        # Constantes
        self.PITCH_CABRAGE = -25000  # Valeur négative pour lever la tête
        
        # Timer principal à 25Hz (0.04s)
        self.timer = self.create_timer(0.04, self.control_loop)
        self.state_timer_counter = 0

    def imu_callback(self, msg):
        # Conversion du quaternion en angle de Pitch (Tangage)
        q = msg.orientation
        sinp = 2 * (q.w * q.y - q.z * q.x)
        if abs(sinp) >= 1:
            pitch_rad = math.copysign(math.pi / 2, sinp)
        else:
            pitch_rad = math.asin(sinp)
        self.current_pitch_deg = math.degrees(pitch_rad)

    def control_loop(self):
        # --- MACHINE À ÉTATS ASYNCHRONE ---
        
        # ÉTAPE 1 : Activation du mode High Step (H-Step)
        if self.state == "INIT":
            self.get_logger().info('Étape 1 : Envoi de la commande H-Step (0x21010407)')
            hstep = MotionSimpleCMD()
            hstep.cmd_code = 0x21010407
            hstep.size = 0
            hstep.type = 0
            self.simple_cmd_pub.publish(hstep)
            
            self.state = "WAIT_FOR_GAIT"
            self.state_timer_counter = 0

        # Attendre ~2 secondes (50 cycles à 25Hz)
        elif self.state == "WAIT_FOR_GAIT":
            self.state_timer_counter += 1
            if self.state_timer_counter >= 50: 
                self.state = "SET_PITCH"

        # ÉTAPE 2 : Cabrage du robot
        elif self.state == "SET_PITCH":
            self.get_logger().info(f'Étape 2 : Cabrage du châssis - Pitch à {self.PITCH_CABRAGE} (0x21010130)')
            pitch_cmd = MotionSimpleCMD()
            pitch_cmd.cmd_code = 0x21010130
            pitch_cmd.size = self.PITCH_CABRAGE
            pitch_cmd.type = 0
            self.simple_cmd_pub.publish(pitch_cmd)
            
            self.state = "WAIT_FOR_PITCH"
            self.state_timer_counter = 0

        # Attendre ~1 seconde (25 cycles à 25Hz)
        elif self.state == "WAIT_FOR_PITCH":
            self.state_timer_counter += 1
            if self.state_timer_counter >= 25:
                self.get_logger().info('Étape 3 : Début de l ascension à 0.27 m/s')
                self.start_time = self.get_clock().now().seconds_nanoseconds()[0]
                self.state = "CLIMBING"

        # ÉTAPE 3 : Ascension active et surveillance de la fin de l'escalier
        elif self.state == "CLIMBING":
            current_time = self.get_clock().now().seconds_nanoseconds()[0]
            elapsed = current_time - self.start_time
            
            is_flat = abs(self.current_pitch_deg) < 5.0
            
            if elapsed > 40.0:
                self.get_logger().warn('Fin de séquence : Temps limite atteint (40s)')
                self.stop_and_reset()
            
            elif elapsed > 15.0 and is_flat:
                self.flat_ground_counter += 1
                if self.flat_ground_counter > 15: # ~0.6s à plat continu
                    self.get_logger().info('Fin de séquence : Haut de l escalier détecté')
                    self.stop_and_reset()
            else:
                self.flat_ground_counter = 0
                
                vel = Twist()
                vel.linear.x = 0.27
                self.cmd_vel_pub.publish(vel)

    def stop_and_reset(self):
        self.state = "FINISHED"
        self.cmd_vel_pub.publish(Twist())
        
        self.get_logger().info('Réinitialisation : Retour au mode marche à plat')
        reset_gait = MotionSimpleCMD()
        reset_gait.cmd_code = 0x21010300
        reset_gait.size = 0
        reset_gait.type = 0
        self.simple_cmd_pub.publish(reset_gait)
        
        reset_pitch = MotionSimpleCMD()
        reset_pitch.cmd_code = 0x21010130
        reset_pitch.size = 0
        reset_pitch.type = 0
        self.simple_cmd_pub.publish(reset_pitch)
        
        self.get_logger().info('Robot stabilisé sur le palier.')
        self.timer.cancel()

def main(args=None):
    rclpy.init(args=args)
    node = BlindClimberNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Arrêt manuel demandé.')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()