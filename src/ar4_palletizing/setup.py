import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'ar4_palletizing'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ahmed',
    maintainer_email='ahmed@example.com',
    description='Palletizing application nodes for the AR4 robot arm '
                '(MoveIt 2 state machine, OpenCV box vision, conveyor interface).',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'palletizing_demo = ar4_palletizing.palletizing_demo:main',
            'vision_node = ar4_palletizing.vision_node:main',
            'conveyor_interface = ar4_palletizing.conveyor_interface:main',
        ],
    },
)
