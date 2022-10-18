from setuptools import setup, find_packages

setup(
    name='gluon',
    version='0.0.1',
    author='Marcel Gietzmann-Sanders',
    author_email='marcelsanders96@gmail.com',
    packages=find_packages(include=['gluon', 'gluon*']),
    install_requires=[
        'httpretty==1.1.4',
        'pytest==7.1.3',
        'requests==2.28.1',
    ]
)