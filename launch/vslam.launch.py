import launch
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    """
    Standalone isaac_ros_visual_slam launch for the Aion R6 rig, run inside the
    Isaac ROS docker container. The front Gemini 336 driver runs separately on the
    host (localisation/launch/camera.launch.py in aion-r6-ROS) -- its topics
    and TF reach this container over DDS, so no camera node is started here.

    base_frame is base_link (robot root); camera_optical_frames are the Gemini 336's
    left/right IR optical frames, which is the stereo pair VSLAM tracks against.
    Images/camera_info come in raw (not pre-rectified) so rectified_images is False --
    VSLAM rectifies internally using each camera_info's distortion model.

    IMU fusion is on, fed from the camera's synced accel+gyro stream (single Imu
    topic/frame, since VSLAM only takes one). gyro/accel noise figures below are
    the same placeholder MEMS values NVIDIA ships in its RealSense example launch,
    not the Gemini 336's actual datasheet numbers -- tune these once known, bad
    values won't break tracking but will make the IMU fusion overconfident.
    """
    visual_slam_node = ComposableNode(
        name='visual_slam_node',
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        parameters=[{
            'enable_image_denoising': False,
            'rectified_images': False,
            'enable_imu_fusion': True,
            'imu_frame': 'camera_accel_gyro_optical_frame',
            'gyro_noise_density': 0.000244,
            'gyro_random_walk': 0.000019393,
            'accel_noise_density': 0.001862,
            'accel_random_walk': 0.003,
            'calibration_frequency': 200.0,
            'base_frame': 'base_link',
            'camera_optical_frames': [
                'camera_left_ir_optical_frame',
                'camera_right_ir_optical_frame',
            ],
            'enable_slam_visualization': True,
            'enable_landmarks_view': True,
            'enable_observations_view': True,
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
