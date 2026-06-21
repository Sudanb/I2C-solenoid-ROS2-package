from setuptools import find_packages, setup

package_name = 'i2c_solenoid_driver'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/i2c_solenoid_driver.launch.py']),
    ],
    install_requires=['setuptools', 'smbus2'],
    zip_safe=True,
    maintainer='Sudan Baral',
    maintainer_email='sudan@example.com',
    description=(
        'MCP23017-based 8-channel I2C solenoid driver, additive alongside '
        'the existing TeeJet CAN sprayer_driver package.'
    ),
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mcp23017_solenoid_node = i2c_solenoid_driver.mcp23017_solenoid_node:main',
        ],
    },
)
