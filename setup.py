from distutils.core import setup

setup(
    name='py-pgtest',
    version='0.1.0',
    packages=['py_pgtest'],
    url='github',
    license='MIT',
    author='Ziyang Hu',
    author_email='hu.ziyang@cantab.net',
    description='testing pg made easy',
    entry_points={
        'console_scripts': ['pgtest=py_pgtest.cli:main'],
    },
    install_requires=['pytest-tap', 'watchdog']
)
