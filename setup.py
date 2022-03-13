from setuptools import setup

setup(
    name='scrapers',
    version='1.0.0',
    url='https://github.com/fwh-ltd/freeones.git',
    author='Tamas Kovacs',
    author_email='no@no.no',
    description='Scrape Freeones.com bios and galleries',
    packages=['scrapers'],
    install_requires=['beautifulsoup4', 'lxml', 'pyyaml', 'requests'],
)
