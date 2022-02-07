from setuptools import setup, find_packages

setup(
    name='freeones',
    version='1.0.0',
    url='https://github.com/fwh-ltd/freeones.git',
    author='Tamas Miklos Kovacs',
    author_email='no@no.no',
    description='Scrape Freeones.com bios and galleries',
    packages=find_packages(),    
    install_requires=['beautifulsoup4','lxml','pyyaml','requests'],
)
