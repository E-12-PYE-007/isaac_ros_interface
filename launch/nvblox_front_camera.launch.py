import os
from ament_index_python.packages import get_package_share_directory
import launch
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    """
    Standalone nvblox launch for the Aion R6 rig, run inside the Isaac ROS
    docker container alongside isaac_ros_visual_slam_front_camera.launch.py.

    There's no NvbloxCamera preset for the Gemini 336 (nvblox_examples_bringup's
    perception/nvblox.launch.py only covers isaac_sim/realsense/zed), so this
    loads nvblox_ros's NvbloxNode directly, the same way the VSLAM launch file
    hand-rolls its ComposableNode rather than using a canned wrapper.

    Pose comes from TF (use_tf_transforms in nvblox_base.yaml, left at its
    default of true) rather than a remapped pose topic -- VSLAM already
    publishes the odom -> base_link chain nvblox looks up per depth frame,
    matching nvblox_ros's default global_frame ('odom'), so no frame params
    are overridden here.

    use_lidar is forced off since nvblox_base.yaml defaults it to true and
    the rig has no lidar.
    """
    # For bringup only - declares static tf to remove dependency on pose est.
    use_static_tf_arg = DeclareLaunchArgument(
        'use_static_tf',
        default_value='true',
        description='Publish a static odom->camera_link TF instead of relying on VSLAM.',
    )

    static_tf_node = Node(
        condition=IfCondition(LaunchConfiguration('use_static_tf')),
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--qx', '0', '--qy', '0', '--qz', '0', '--qw', '1',
            '--frame-id', 'odom',
            '--child-frame-id', 'base_link',
        ],
        output='screen',
    )


    nvblox_base_config = os.path.join(
        get_package_share_directory('nvblox_examples_bringup'),
        'config', 'nvblox', 'nvblox_base.yaml',
    )

    nvblox_node = ComposableNode(
        name='nvblox_node',
        package='nvblox_ros',
        plugin='nvblox::NvbloxNode',
        parameters=[
            nvblox_base_config,
            {
                'use_lidar': False,
                'voxel_size': 0.05,
                'integrate_depth_rate_hz': 15.0,
                'integrate_color_rate_hz': 2.0,
                'update_mesh_rate_hz': 0.0, # Mesh is cosmetic only - not required
                'update_esdf_rate_hz': 10.0,
                'publish_layer_rate_hz': 2.0,
                'publish_debug_vis_rate_hz': 0.0,
                'use_color': True,
                # Using height_bounds to constrain vertical range only.
                # For a bounded area (e.g. fenced plot), switch to:
                #   'static_mapper.workspace_bounds_type': "bounding_box",
                #   'static_mapper.workspace_bounds_min_corner_x_m': -5.0,
                #   'static_mapper.workspace_bounds_min_corner_y_m': -5.0,
                #   'static_mapper.workspace_bounds_max_corner_x_m': 5.0,
                #   'static_mapper.workspace_bounds_max_corner_y_m': 5.0,
                #   'dynamic_mapper.workspace_bounds_type': "bounding_box",
                #   'dynamic_mapper.workspace_bounds_min_corner_x_m': -5.0,
                #   'dynamic_mapper.workspace_bounds_min_corner_y_m': -5.0,
                #   'dynamic_mapper.workspace_bounds_max_corner_x_m': 5.0,
                #   'dynamic_mapper.workspace_bounds_max_corner_y_m': 5.0,
                # Corners are relative to the odom frame origin (robot start pose).
                'static_mapper.workspace_bounds_type': "height_bounds",
                'static_mapper.workspace_bounds_min_height_m': 0.1,
                'static_mapper.workspace_bounds_max_height_m': 1.0,
                'dynamic_mapper.workspace_bounds_type': "height_bounds",
                'dynamic_mapper.workspace_bounds_min_height_m': 0.1,
                'dynamic_mapper.workspace_bounds_max_height_m': 1.0,
                'static_mapper.esdf_slice_height': 0.0,
            },
        ],

        remappings=[
            ('camera_0/depth/image', '/front_camera/depth/image_raw'),
            ('camera_0/depth/camera_info', '/front_camera/depth/camera_info'),
            ('camera_0/color/image', '/front_camera/color/image_raw'),
            ('camera_0/color/camera_info', '/front_camera/color/camera_info'),
        ],
    )

    nvblox_launch_container = ComposableNodeContainer(
        name='nvblox_launch_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[nvblox_node],
        output='screen',
    )

    return launch.LaunchDescription([
        use_static_tf_arg,
        static_tf_node,
        nvblox_launch_container,
    ])