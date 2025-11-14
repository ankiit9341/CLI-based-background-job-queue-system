from setuptools import setup, find_packages

setup(
    name='queuectl',
    version='1.0.0',
    description='A CLI-based background job queue system for internship assignment',
    author='Ankit Kumar Yadav',
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=[
        'click==8.1.7',
    ],
    entry_points={
        'console_scripts': [
            'queuectl = queuectl.cli:cli',
        ],
    },
)
