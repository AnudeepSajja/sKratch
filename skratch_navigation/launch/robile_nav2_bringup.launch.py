import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def generate_launch_description():

    # -------------------------
    # Directories and environment
    # -------------------------
    skratch_nav_dir = get_package_share_directory('skratch_navigation')
    skratch_desc_dir = get_package_share_directory('skratch_description')

    # Use ROBOT_ENV or default
    map_name = os.environ.get('ROBOT_ENV', 'sim_map')
    map_file = os.path.join(skratch_nav_dir, 'maps', map_name + '.yaml')

    use_sim_time = True

    # -------------------------
    # Map Server Node
    # -------------------------
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'yaml_filename': map_file,
            'frame_id': 'map'
        }]
    )

    # -------------------------
    # Lifecycle Manager
    # -------------------------
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_mapper',
        output='screen',
        emulate_tty=True,
        parameters=[{
            'use_sim_time': use_sim_time,
            'autostart': True,
            'node_names': ['map_server']
        }]
    )

    # -------------------------
    # Static Transform Publisher
    # -------------------------
    tf2_ros = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--roll', '0', '--pitch', '0', '--yaw', '0',
            '--frame-id', 'map', '--child-frame-id', 'odom'
        ]
    )

    # -------------------------
    # Include Localization Launch
    # -------------------------
    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(skratch_nav_dir, 'launch', 'localization.launch.py')
        )
    )

    # -------------------------
    # Include Navigation Launch
    # -------------------------
    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(skratch_nav_dir, 'launch', 'navigation.launch.py')
        )
    )

    # -------------------------
    # RViz Node
    # -------------------------
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(skratch_desc_dir, 'rviz', 'navigation.rviz')],
        output='screen'
    )

    # -------------------------
    # Launch Description
    # -------------------------
    return LaunchDescription([
        map_server,
        lifecycle_manager,
        tf2_ros,
        localization_launch,
        navigation_launch,
        rviz_node
    ])
