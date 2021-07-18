******************
:mod:`spy.prelude`
******************

Utilities that are automatically imported during spy runs and of little
use elsewhere.

.. module:: spy.prelude

.. function:: id(x)

   Return ``x``.

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

   Exactly like the built-in sum, but written with generic usage in mind: this
   version accepts anything for which `+` is defined, and avoids quadratic
   behaviour where possible.
