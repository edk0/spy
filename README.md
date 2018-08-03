[![Build Status](https://travis-ci.org/edk0/spy.svg?branch=master)](https://travis-ci.org/edk0/spy)
[![Coverage Status](https://img.shields.io/coveralls/edk0/spy.svg)](https://coveralls.io/r/edk0/spy?branch=master)

# spy: a Python CLI

`spy` stands for “<b>s</b>tream <b>py</b>thon”. It's a CLI for python that
chains fragments of code together. It's inspired by
[pyp](https://code.google.com/p/pyp/) and
[pythonpy](https://github.com/Russell91/pythonpy), and is intended to fill a
similar role to that of `sed`.

I built spy primarily because I wanted a more pure interface than either of the
above offer; I'd like to think I succeeded, but I'm sure it can be improved
upon, so please let me know if you find anything wrong with it.

**spy is unreleased software**. You can install it if you want, but please
don't expect reliability or stability—I'll make a release when I have those
things. If that's okay, `pip install 'spy-cli>0a0'`.

spy is compatible with Python 3.4 and newer.

**The docs, including introduction, are available
[on ReadTheDocs](https://spy.readthedocs.org/en/latest/).**

If you have any suggestions or feedback or anything, I'll probably be in`#spy`
on `irc.freenode.net`.

# Example ([more here](https://spy.readthedocs.org/en/latest/examples.html))

```console
$ spy -l -f 'len(pipe) == 4' < /usr/share/dict/words
Aani
Aaru
abac
abas
Abba
Abby
abed
Abel
abet
abey
…
```
