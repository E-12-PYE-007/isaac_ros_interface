import launch
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    """
    Standalone isaac_ros_visual_slam launch for the Aion R6 robot, run inside the
    Isaac ROS 3.2 docker container. The front Gemini 336 driver runs separately on
    the host -- its topics and TF reach this container over DDS.

    VIO is enabled. Stereo IR + the Gemini 336's synced accel/gyro
    stream.

    VSLAM publishes no TF: the EKF owns odom->base_link, and map->odom
    must be computed against the EKF's odom (relay or global EKF), not published by
    VSLAM. VO output is consumed by the VO relay (twist + measured covariance),
    stamped in 'vo_odom' so it is never mistaken for the EKF's odom frame.

    SLAM is enabled. Ground constraints (odometry + SLAM) flatten poses onto the
    start plane: valid for flat-floor operation only.

    Driver-side requirements (host, OrbbecSDK_ROS2): enable_laser: false,
    time_domain: device, enable_sync_host_time: true.
    """
    visual_slam_node = ComposableNode(
        name='visual_slam_node',
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        parameters=[{
            # tracking mode + images
            'enable_imu_fusion': True,          # VIO
            'num_cameras': 2,
            'rectified_images': True,           
                                                
            'enable_image_denoising': False,

            # IMU (VIO)
            'imu_frame': 'camera_accel_gyro_optical_frame',  
            'gyro_noise_density': 3.2e-05,    
            'gyro_random_walk': 2.0e-06,   
            'accel_noise_density': 0.0004,    
            'accel_random_walk': 8.0e-05,       
            'calibration_frequency': 200.0,    
            'imu_buffer_size': 50,              # ~250 ms at 200 Hz; stored as uint8

            # timing
            'image_jitter_threshold_ms': 40.0,  # IR at 29.99 Hz (33.3 ms period, max seen 35 ms)
            'sync_matching_threshold_ms': 5.0,  
            'override_publishing_stamp': False, 

            # frames + TF
            'base_frame': 'base_link',
            'odom_frame': 'vo_odom', 
            'map_frame': 'map',
            'camera_optical_frames': [
                'camera_left_ir_optical_frame',  
                'camera_right_ir_optical_frame', 
            ],
            # TEMP: True to test VSLAM 
            'publish_odom_to_base_tf': True,   # EKF owns odom->base_link
            'publish_map_to_odom_tf': True,    # TODO Decide who owns this - VSLAM or EKF
            
            # SLAM
            'enable_localization_n_mapping': True,
            'enable_ground_constraint_in_slam': True, 
            'slam_max_map_size': 300,                   # TODO: determine appropriate value
            'slam_throttling_time_ms': 500,
            'save_map_folder_path': '',                 # TODO: set if we want to save maps
            'load_map_folder_path': '',                 # TODO: maybe if we ever use the same setup
            'localize_on_startup': False,               # TODO: True to localize in load_map_folder_path at start
            'enable_ground_constraint_in_odometry': True,

            # Visualisations
            'enable_slam_visualization': False,
            'enable_landmarks_view': False,
            'enable_observations_view': False,
        }],
        remappings=[
            ('visual_slam/image_0', '/camera/left_ir/image_raw'),
            ('visual_slam/camera_info_0', '/camera/left_ir/camera_info'),
            ('visual_slam/image_1', '/camera/right_ir/image_raw'),
            ('visual_slam/camera_info_1', '/camera/right_ir/camera_info'),
            ('visual_slam/imu', '/camera/gyro_accel/sample'),
        ],
    )

    visual_slam_launch_container = ComposableNodeContainer(
        name='visual_slam_launch_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[visual_slam_node],
        output='screen',
    )

    return launch.LaunchDescription([visual_slam_launch_container])
