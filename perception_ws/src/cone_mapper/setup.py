from setuptools import find_packages, setup

package_name = 'cone_mapper'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Cardiff Autonomous Racing',
    maintainer_email='cardiff@racing.ac.uk',
    description='Builds local and global cone maps from YOLO detections and SLAM pose',
    license='MIT',
    entry_points={
        'console_scripts': [
            'cone_mapper = cone_mapper.cone_mapper:main',
        ],
    },
)
