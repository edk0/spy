from setuptools import setup

setup(
    name='spy-cli',
    version='0.1',
    packages=['spy'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'spy = spy.main:main'
        ]
    },
    install_requires=['clize'],
    author = 'Ed Kellett',
    author_email = 'edk@kellett.im',
    url = 'https://github.com/edk0/spy/'
)
