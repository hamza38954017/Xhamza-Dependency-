from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='xhamza',
    version='1.0.1', # Change this if you update your code later
    description='A simple tool to extract m3u8  links of xhamster video.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Hamza',
    packages=find_packages(),
    install_requires=[
        'curl_cffi>=0.5.10'
    ],
    entry_points={
        'console_scripts': [
            'xhamza=xhamza.core:main',
        ],
    },
)
