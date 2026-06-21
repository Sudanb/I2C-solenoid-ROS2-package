from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    min_det_arg = DeclareLaunchArgument(
        'min_detections_to_spray', default_value='3')
    spray_duration_arg = DeclareLaunchArgument(
        'spray_duration', default_value='0.762')
    cooldown_arg = DeclareLaunchArgument(
        'cooldown_duration', default_value='1.0')
    image_height_arg = DeclareLaunchArgument(
        'image_height', default_value='640')

    zone_trigger_node = Node(
        package='aphid_zone_trigger',
        executable='aphid_zone_trigger_node',
        name='aphid_zone_trigger',
        output='screen',
        parameters=[{
            'min_detections_to_spray': LaunchConfiguration('min_detections_to_spray'),
            'spray_duration': LaunchConfiguration('spray_duration'),
            'cooldown_duration': LaunchConfiguration('cooldown_duration'),
            'image_height': LaunchConfiguration('image_height'),
        }],
    )

    return LaunchDescription([
        min_det_arg,
        spray_duration_arg,
        cooldown_arg,
        image_height_arg,
        zone_trigger_node,
    ])
