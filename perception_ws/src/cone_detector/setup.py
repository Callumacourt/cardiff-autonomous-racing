from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'cone_detector'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Cardiff Autonomous Racing',
    maintainer_email='callumacourtt@gmail.com',
    description='YOLOv8-based cone detector for autonomous racing',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'cone_detector_node = cone_detector.cone_detector_node:main',
        ],
    },
)
