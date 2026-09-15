import launch
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    """
    Standalone isaac_ros_visual_slam launch for the Aion R6 rig, run inside the
    Isaac ROS docker container. The front Gemini 336 driver runs separately on the
    host -- its topics and TF reach this container over DDS, so no camera node is
    started here.

    Tracking mode is VIO (tracking_mode: 1): stereo IR + the Gemini 336's synced
    accel/gyro stream. The robot EKF must NOT also fuse the Gemini IMU (it would be
    counted twice); the robot's own IMUs are fused in the EKF instead.

    The driver publishes the IR pair already rectified (camera_info d = 0, R = I,
    identical K; left->right is a pure 50 mm x-translation), so rectified_images is
    True. cuVSLAM uses the plain pinhole model and fast row-aligned stereo matching.

    VSLAM publishes no odom->base_link TF: the EKF owns it. VO output is consumed by
    the VO relay (twist + measured covariance), stamped in 'vo_odom' so it is never
    mistaken for the EKF's odom frame.

    Driver-side requirements (host, OrbbecSDK_ROS2): enable_laser: false,
    time_domain: device, enable_sync_host_time: true.
    """
    visual_slam_node = ComposableNode(
        name='visual_slam_node',
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        parameters=[{
            # tracking mode + images
            'tracking_mode': 1,                 # VIO: stereo + IMU fusion
            'num_cameras': 2,
            'rectified_images': True,           # driver outputs rectified IR (verified). If the node throws
                                                # "Rotation matrices of cameras 0 and 1 differ", set False
            'enable_image_denoising': False,

            # IMU (VIO)
            'imu_frame': 'camera_accel_gyro_optical_frame',  # verified: matches IMU header.frame_id
            'gyro_noise_density': 3.2e-05,     # TODO: Gemini 336 datasheet value [rad/s/sqrt(Hz)] (placeholder)
            'gyro_random_walk': 2.0e-06,    # TODO: Gemini 336 datasheet value [rad/s^2/sqrt(Hz)] (placeholder)
            'accel_noise_density': 0.0004,    # TODO: Gemini 336 datasheet value [m/s^2/sqrt(Hz)] (placeholder)
            'accel_random_walk': 8.0e-05,         # TODO: Gemini 336 datasheet value [m/s^3/sqrt(Hz)] (placeholder)
            'calibration_frequency': 200.0,     # measured IMU rate [Hz]
            'imu_buffer_size': 50,              # ~250 ms at 200 Hz; stored as uint

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
            'publish_odom_to_base_tf': False,   # EKF owns odom->base_link
            'publish_map_to_odom_tf': False,    # TODO Decide who owns this - VSLAM or EKF
            
            # SLAM
            'enable_localization_n_mapping': True,
            'enable_ground_constraint_in_slam': True, 
            'slam_max_map_size': 300,                   # TODO: determine appropriate value
            'slam_throttling_time_ms': 500,
            'save_map_folder_path': '/home/vla-cap/testing/vslam/maps',                 
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
