import os.path

from setuptools import setup


readme = os.path.join(os.path.dirname(__file__), 'README.md')
with open(readme) as f:
    long_description = f.read()


setup(
    name='spy-cli',
    version='0.3.2',
    description='stream processing Python CLI',
    packages=['spy'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'spy = spy.cli:main'
        ]
    },
    install_requires=[
        'clize>=3.0',
    ],
    extras_require={
        'test': [
            'pytest',
            'pytest-cov',
            'coverage',
        ]
    },
    author='Ed Kellett',
    author_email='e@kellett.im',
    url='https://github.com/edk0/spy/',
    project_urls={
        'Documentation': 'https://spy.readthedocs.io/',
    },
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: Public Domain',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities'
    ]
)
