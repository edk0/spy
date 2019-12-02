[![Build Status](https://travis-ci.org/edk0/spy.svg?branch=master)](https://travis-ci.org/edk0/spy)
[![Coverage Status](https://coveralls.io/repos/github/edk0/spy/badge.svg?branch=master)](https://coveralls.io/github/edk0/spy?branch=master)

# spy: a Python CLI

```
pip install spy-cli
```

`spy` stands for “<b>s</b>tream <b>py</b>thon”. It's a CLI for python that
chains fragments of code together. It's inspired by
[pyped](https://github.com/ksamuel/Pyped) and
[pythonpy](https://github.com/Russell91/pythonpy).

I built spy primarily because I wanted a more pure interface than either of the
above offer; I'd like to think I succeeded, but I'm sure it can be improved
upon, so please let me know if you see a way to make it nicer.

spy is compatible with, and thoroughly tested on, Python 3.5 and newer.

**The docs, including introduction, are available
[on ReadTheDocs](https://spy.readthedocs.org/en/stable/).**

If you have any suggestions or feedback or anything, I'll probably be in `#spy`
on `irc.freenode.net`.

# Example ([more here](https://spy.readthedocs.org/en/stable/examples.html))

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
