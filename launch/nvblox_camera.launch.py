import os
from ament_index_python.packages import get_package_share_directory
import launch
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    
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
                'global_frame': 'odom',  # TEMP: testing nvblox without VSLAM; restore 'map'
                'voxel_size': 0.1,
                'integrate_depth_rate_hz': 5.0,
                'integrate_color_rate_hz': 0.0,
                'update_mesh_rate_hz': 0.0,
                'update_esdf_rate_hz': 5.0,
                'publish_layer_rate_hz': 5.0,
                'publish_debug_vis_rate_hz': 0.0,
                'use_color': True,

                'map_clearing_radius_m': 3.0,
                'map_clearing_frame_id': 'base_link',
                'clear_map_outside_radius_rate_hz': 0.5,

                'static_mapper.workspace_bounds_type': "height_bounds",
                'static_mapper.workspace_bounds_min_height_m': 0.1,
                'static_mapper.workspace_bounds_max_height_m': 0.2,
                'dynamic_mapper.workspace_bounds_type': "height_bounds",
                'dynamic_mapper.workspace_bounds_min_height_m': 0.1,
                'dynamic_mapper.workspace_bounds_max_height_m': 0.2,
                'static_mapper.esdf_slice_height': 0.0,
                'static_mapper.projective_integrator_max_integration_distance_m': 2.0,
            },
        ],

        remappings=[
            ('camera_0/depth/image', '/camera/depth/image_raw'),
            ('camera_0/depth/camera_info', '/camera/depth/camera_info'),
            ('camera_0/color/image', '/camera/color/image_raw'),
            ('camera_0/color/camera_info', '/camera/color/camera_info'),
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

    return launch.LaunchDescription([nvblox_launch_container])