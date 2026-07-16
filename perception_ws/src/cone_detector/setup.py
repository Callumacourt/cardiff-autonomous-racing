from setuptools import find_packages, setup

package_name = 'cone_detector'

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
    description='YOLOv8 cone detection with depth-based 3D localisation',
    license='MIT',
    entry_points={
        'console_scripts': [
            'YOLO_cone_detector = cone_detector.YOLO_cone_detector:main',
        ],
    },
)
