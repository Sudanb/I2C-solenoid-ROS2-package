from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    i2c_bus_arg = DeclareLaunchArgument(
        'i2c_bus', default_value='7',
        description='I2C bus number for the MCP23017 board (check with i2cdetect on AGX Orin)'
    )
    i2c_address_arg = DeclareLaunchArgument(
        'i2c_address', default_value='32',  # 0x20
        description='I2C address of the MCP23017 board (decimal; default 0x20 = 32)'
    )

    solenoid_node = Node(
        package='i2c_solenoid_driver',
        executable='mcp23017_solenoid_node',
        name='mcp23017_solenoid_driver',
        output='screen',
        parameters=[{
            'i2c_bus': LaunchConfiguration('i2c_bus'),
            'i2c_address': LaunchConfiguration('i2c_address'),
            'active_high': True,
        }],
    )

    return LaunchDescription([
        i2c_bus_arg,
        i2c_address_arg,
        solenoid_node,
    ])
