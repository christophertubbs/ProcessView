from setuptools import setup

setup(
    name='ProcessView',
    version='0.1',
    packages=['models', 'handlers', 'utilities'],
    package_dir={'': 'pview'},
    url='https://github.com/christophertubbs/ProcessView',
    license='MIT',
    author='christopher.tubbs',
    author_email='',
    description='A simple local application used to show and explore local process utilization '
)
