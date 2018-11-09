from distutils.core import setup
import setuptools

setup(
    name='py-pgtest',
    version='0.1.7',
    packages=['py_pgtest'],
    url='https://github.com/zh217/py-pgtest',
    license='MIT',
    author='Ziyang Hu',
    author_email='hu.ziyang@cantab.net',
    description='testing pg made easy',
    entry_points={
        'console_scripts': ['pgtest=py_pgtest.cli:main'],
    },
    install_requires=['pytest-tap', 'watchdog', 'colorama'],
    include_package_data=True
)
