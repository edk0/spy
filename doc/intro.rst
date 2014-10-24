************
Introduction
************

spy is a Python CLI. It's quite powerful, as you'll see below, but let's start
with the basics: you feed it a Python expression, it spits out the result.

.. code-block:: console

   $ spy '3*4'
   12

There's no need to import modules—just use them and spy will make sure they're
available:

.. code-block:: console

   $ spy 'math.pi'
   3.141592653589793


I/O
===

Standard input is exposed as a file-like object called ``pipe``:

.. code-block:: console

   $ cat test.txt
   this
   file
   has
   five
   lines
   $ spy 'pipe.readline()' < test.txt
   this

It's a full-featured :class:`io.TextIOBase`, but is extended with other
useful features: indexing (even slicing) and string methods:

.. code-block:: console

   $ spy 'pipe[1]' < test.txt
   file
   $ spy 'pipe[1::2]' < test.txt
   ['file', 'five']
   $ spy 'pipe.replace("\n", " ")' < test.txt
   this file has five lines

Passing ``-l`` (or ``--each-line``) to spy will iterate through stdin instead,
so your expressions will run once per line of input:

.. code-block:: console

   $ spy -l '"-%s-" % pipe' < test.txt
   -this-
   -file-
   -has-
   -five-
   -lines-


Piping
======

Much like the standard assortment of unix utilities, which expect to have their
inputs and outputs wired up to each other in order to do useful things, each
fragment processes some data then passes it on to the next one.

Data passes from left to right. Fragments can return the special constant
:const:`spy.DROP` to prevent further processing of the current datum and
continue to the next.

.. code-block:: console

   $ spy '3' 'pipe * 2' 'pipe * "!"'
   !!!!!!
   $ spy -l 'if pipe.startswith("f"): pipe = spy.DROP' < test.txt
   this
   has
   lines


Limiting output
===============

.. option:: --start=<integer>, -s <integer>

   Start printing output at this zero-based index.

.. option:: --end=<integer>, -e <integer>

   Stop processing at this zero-based index.

``-s`` and ``-e`` mirror Python's slice semantics, so ``-s 1 -e 3`` will show
results 1 and 2. This means ``-e`` on its own is equivalent to a limit on the
number of results.

Once the result specified by ``-e`` has been hit, no more data will be
processed.


Data flow
=========

Before I explain this, a brief discourse into how data moves around in spy: Each
fragment in spy tries to consume data from the fragment to its left. It
processes it, then yields to the fragment to its right, which will do the same
thing. To run the program, spy just tries to pump as much data out of the
rightmost fragment as it can—everything else is handled by the fragment
mechanic.

In the examples I've given above, each fragment has consumed and yielded data on
a one-to-one basis, but there's no inherent reason for that restriction.
Fragments can yield or consume (or both) multiple values using
:class:`spy.many` and :class:`spy.collect`, respectively.


Decorators
==========

In one example above, we used an ``if`` statement to filter by a predicate.
That's far from elegant—by my rough guess, about half the characters in the
fragment are boilerplate. spy provides some function decorators to avoid
repeating this and a few other common constructs—they're available as flags from
the CLI:

.. option:: --callable <fragment>, -c <fragment>

   calls whatever the following fragment returns, with a single argument: the
   input value to the fragment.

.. option:: --filter <fragment>, -f <fragment>

   filters the data stream, using the fragment as a predicate: if it returns
   any true value, the data passes through, but if it returns a false value
   :const:`spy.DROP` is returned instead.

.. option:: --many <fragment>, -m <fragment>

   calls :py:func:`spy.many` with the return value of the fragment (which must
   be :term:`iterable`).

.. option:: --once <fragment>, -o <fragment>

   executes its fragment at most once. Its return value is completely ignored;
   any data going in is passed through unchanged.


Exception handling
==================

If your code raises an uncaught exception, spy will try to intercept and
reformat the traceback, omitting the frames from spy's own machinery. Special
frames will be inserted where appropriate describing the fragment's position,
source code, and input data at the time the exception was raised:

.. code-block:: console

   $ spy 'None + 2'
   Traceback (most recent call last):
     Fragment 1
       None + 2
       input to fragment was <SpyFile stream=<_io.TextIOWrapper name='<stdin>' mode='r' encoding='UTF-8'>>
   TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'

If an exception is raised in a decorator outside the call to the fragment body,
the fragment is mentioned anyway. This is not strictly true, given that none of
the code in the fragment takes part in the call stack in this case, but this
particular lie is almost universally more useful:

.. code-block:: console

   $ spy -c None
   Traceback (most recent call last):
     Fragment 1, in decorator spy.decorators.callable
       --callable 'None'
       input to fragment was <SpyFile stream=<_io.TextIOWrapper name='<stdin>' mode='r' encoding='UTF-8'>>
     File "/home/edk/src/spy/spy/decorators.py", line 44, in callable
       return result(v)
   TypeError: 'NoneType' object is not callable

The philosophy here is that what made it go wrong is more interesting than
*exactly how* it went wrong, so that's what spy gives you by default. You can
get the real traceback by passing ``--no-exception-handling`` to spy.
