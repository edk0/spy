from setuptools import setup

setup(
    name='spy-cli',
    version='0.1a2',
    description='stream processing Python CLI',
    packages=['spy'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'spy = spy.cli:main'
        ]
    },
    install_requires=['clize>=3.0a1'],
    author = 'Ed Kellett',
    author_email = 'edk@kellett.im',
    url = 'https://github.com/edk0/spy/',
    long_description = 'See https://github.com/edk0/spy/blob/master/README.md',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: Public Domain',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Utilities'
    ]
)
