from setuptools import setup, find_packages

setup(
    name='pytracto',
    version='0.1',
    packages=find_packages(),
    install_requires=['python-on-whales>=0.71','pybids>=0.16','nipype>=1.8.6','dmri-amico>=2.0.1','connectomemapper>=3.10']
)
