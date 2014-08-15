from setuptools import setup

setup(
    name='spy-cli',
    version='0.1a1',
    description='stream processing Python CLI',
    packages=['spy'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'spy = spy.main:main'
        ]
    },
    install_requires=['clize>=3.0a1'],
    author = 'Ed Kellett',
    author_email = 'edk@kellett.im',
    url = 'https://github.com/edk0/spy/',
    long_description = 'See https://github.com/edk0/spy/blob/master/README.md'
)
