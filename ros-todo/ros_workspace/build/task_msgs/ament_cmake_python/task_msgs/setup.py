from setuptools import find_packages
from setuptools import setup

setup(
    name='task_msgs',
    version='0.0.0',
    packages=find_packages(
        include=('task_msgs', 'task_msgs.*')),
)
