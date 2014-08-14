
# spy: a Python CLI

`spy` stands for “<b>s</b>tream <b>py</b>thon”. It's a CLI for python that chains
fragments of code together.

## Introduction

spy operates on fragments of Python code. In the simplest of invocations, just
feed it an expression and get a result back:

```console
$ spy '3*4'
12
```

Statements are fine too:

```console
$ spy 'print(17*19)'
323
```

Imports are automatic:

```console
$ spy 'math.pi'
3.141592653589793
```

### I/O

Standard input is exposed as a file-like object, called `pipe`:

```console
$ cat test.txt
this
file
has
five
lines
$ spy 'pipe.readline()' < test.txt
this
```

Despite its file-likeness, `pipe` has string methods that act on all the
input at once:

```console
$ spy -l '"-%s-" % pipe' < test.txt
-this-
-file-
-has-
-five-
-lines-
```

Suites of statements don't yield values, but can achieve the same end by
assigning to `pipe`:

```console
$ spy 's = pipe.readline(); pipe = s.upper()' < test.txt
THIS
```

Passing `-l` (or `--each-line`) to `spy` will iterate through the lines of
input, running your code for each one:

```console
$ spy -l 'pipe.upper()' < test.txt
THIS
FILE
HAS
FIVE
LINES
```

With `-l`, `pipe` will be a simple `str` during each iteration.

### Piping

If you wondered why it was called `pipe`, here you go: Given multiple
fragments, each fragment will receive the value returned by the previous
fragment in the `pipe` variable.

This might be best explained with an example:

```console
$ spy '3' 'pipe * 2' 'pipe * "!"'
!!!!!!
```

Fragments can return `spy.DROP` to prevent further processing:

```console
$ spy -l 'if pipe.startswith("f"): pipe = spy.DROP' < test.txt
this
has
lines
```

### Limiting output

`-s` and `-e` (`--start` and `--end`) set the range of indexes of results
to be displayed. Both are zero-based, `-s` is inclusive and `-e` is
exclusive. I know it sounds a bit stupid, but it means `-e` on its own
is like a 'limit' parameter:

```console
$ spy -l -e 2 'pipe.title()' < test.txt
This
File
...
```

### Data flow

spy fragments try to consume data from the previous fragment. This is
processed by the given expression, and the returned value is then yielded
for consumption by the next fragment. In the examples I've given so far,
there's been a one-to-one correspondence between these processes, but it's
sometimes more convenient to change this.

spy provides two functions to deal with this: `spy.many` and `spy.collect`.

Returning `spy.many(iterable)` makes a fragment yield all the values from
`iterable`. We can use this, for example, to process each word in a file:


```console
$ cat test-many.txt
this
file
has a large number
of things
in
it
$ spy -l 'spy.many(pipe.split())' 'pipe.title()' < test-many.txt
This
File
Has
A
Large
Number
Of
Things
In
It
```

`spy.collect` is more or less the opposite of `spy.many`, and returns an
iterator that yields data from the previous fragment. We can use this to
collect the results from the previous example into one string:

```console
$ spy -l 'spy.many(pipe.split())' 'pipe.title()' '" ".join(spy.collect())' < test-many.txt
This File Has A Large Number Of Things In It
```

Or combine it with `itertools.islice` to make groups of words:

```console
$ spy -l 'spy.many(pipe.split())' 'itertools.islice(spy.collect(), 3)' '" ".join(pipe)' < test-many.txt
this file has
a large number
of things in
it
```

Note that while useful, `spy.collect` can easily be a source of headaches.
Don't use it unless you have a good grasp of how Python iterables work.

### A note on built-in fragments

By default, spy adds extra fragments to the chain to make the interface
easier. We *can* do the same job with the CLI instead—the following commands
are equivalent:

```console
$ spy 'pipe.upper()' < test.txt
$ spy --no-default-fragments 'spy.objects.SpyFile(sys.stdin)' 'pipe.upper()' 'spy.fragments.pretty_print(pipe)' < test.txt
```

In order for CLI fragments to run at all, given that they expect values to
be yielded, the first fragment in the chain is given an iterator that yields
a single `None`.

`-l` is equivalent to a fragment of `spy.many(pipe)` just before the first
user-supplied fragment.

`-s` and `-e` are roughly equivalent to
`spy.many(itertools.islice(spy.collect(), START, END))` just before the print
fragment.

## Examples

### Count words beginning with each letter

```console
$ spy 'collections.Counter(w[0].lower() for w in pipe).most_common(5)' < /usr/share/dict/words
[('s', 25031), ('p', 24412), ('c', 19861), ('a', 17061), ('u', 16387)]
```

### TODO add more of these
