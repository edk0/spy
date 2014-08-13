from setuptools import setup

setup(
    name='spy',
    version='0.1',
    packages=['spy'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'spy = spy.main:main'
        ]
    },
    install_requires=['clize']
)
