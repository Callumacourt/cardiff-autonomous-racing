from setuptools import setup, find_packages

package_name = 'landmark_slam'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Cardiff Autonomous Racing',
    maintainer_email='cardiff@racing.ac.uk',
    description='EKF-SLAM using cone landmarks for Formula Student AI',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'landmark_slam = landmark_slam.landmark_slam_node:main',
        ],
    },
)
