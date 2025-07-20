from setuptools import setup

package_name = 'ros_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='thomas',
    maintainer_email='thomas@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            "command_node = ros_control.cmd_node:main",
            "driving_flag_pub = ros_control.driving_flag_pub:main",
            "mission_flag_pub = ros_control.mission_flag_pub:main",
            "model_predictive_control = ros_control.model_predictive_control:main",
            "mock_control = ros_control.mock_control:main",
            "simple_control_node = ros_control.simple_control_node:main",
        ],
    },
)
