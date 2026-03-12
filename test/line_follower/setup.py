from setuptools import setup

package_name = 'line_follower'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/line_follower.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='team',
    maintainer_email='2093667965@qq.com',
    description='Line following with red-dot stop for Gazebo Harmonic simulation',
    license='MIT',
    entry_points={
        'console_scripts': [
            'line_follower = line_follower.line_follower_node:main',
        ],
    },
)
