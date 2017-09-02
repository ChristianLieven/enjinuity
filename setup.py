"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

requirements = [
    "lxml",
    "selenium"
]

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    readme = f.read()

setup(
    name='Enjinuity',
    version='0.1',
    description='Enjin forum export to MyBB 1.8.',
    long_description=readme,
    url='https://github.com/spikeh/enjinuity',
    author='David H. Wei',
    author_email='nothing@nowhere.com',
    license='CC0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Enjin Users',
        'Topic :: Forum :: Export',
        'License :: OSI Approved :: Creative Commons Zero v1.0 Universal',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='enjin forum scraper',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=requirements,
    # extras_require={
    #     'dev': ['check-manifest'],
    #     'test': ['coverage'],
    # },
)
