import os
from glob import glob
from setuptools import setup

package_name = 'lite3_stair_nav'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.launch.py'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ysc',
    maintainer_email='ysc@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'rgbd_climb = lite3_stair_nav.rgbd_node:main',
            'lidar_climb = lite3_stair_nav.lidar_node:main',
            'blind_climb = lite3_stair_nav.blind_climb:main',
            'stair_climber_control = lite3_stair_nav.stair_climber_control:main',
        ],
    },
)
