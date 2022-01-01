******************
:mod:`spy.prelude`
******************

Utilities that are automatically imported during spy runs. Specfically, the CLI
runs the equivalent of ``from builtins import *; from spy.prelude import *``
before it starts running user code.

.. module:: spy.prelude

.. function:: id(x)

   Return ``x``.

.. function:: exhaust(iterable)

   Iterate over ``iterable`` for its side effects, returning nothing.

.. function:: ft(\*args)

   Return a tuple that, when called, calls all its members with the
   same argument.

.. function:: mt(\*args)

   Return a tuple that, when called, calls each of its members with
   corresponding arguments from the call:

   .. code-block:: console

      $ spy '"abcde", [1,2,3]' -c 'mt(len, sum)'
      (5, 6)

.. function:: sum(iterable, start=0)

   Like the built-in sum, but written with generic usage in mind: this version
   accepts anything for which `+` is defined, and avoids quadratic behaviour
   where possible.

   This depends on in-place addition's being consistent with basic addition.
   The Python documentation does guarantee this, but some significant libraries
   don't.

   If ``start`` is not provided, spy's sum will use ``iterable``'s first
   element, if it has one. Thus ``-ac sum`` will normally just work.
