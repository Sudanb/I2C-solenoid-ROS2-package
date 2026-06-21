from setuptools import find_packages, setup

package_name = 'aphid_zone_trigger'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/aphid_zone_trigger.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Sudan Baral',
    maintainer_email='sudan@example.com',
    description=(
        'Standalone zoned nozzle trigger from aphid detections — '
        'additive, does not touch aphid_sprayer_bridge or sprayer_driver.'
    ),
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'aphid_zone_trigger_node = aphid_zone_trigger.aphid_zone_trigger_node:main',
        ],
    },
)
