from setuptools import setup

setup(
    name='babescrapers',
    version='1.2.0',
    url='https://github.com/fwh-ltd/freeones.git',
    author='Tamas Kovacs',
    author_email='no@no.no',
    description='Scrape Freeones.com bios and galleries',
    packages=['babescrapers'],
    install_requires=['beautifulsoup4', 'lxml', 'pyyaml', 'requests'],
)
