*********************
:mod:`spy.decorators`
*********************

This module contains various function decorators for use in spy fragments.

.. module:: spy.decorators

.. decorator:: accumulate

   .. option:: --accumulate, -a

   Accumulate values into an iterator by calling :func:`spy.collect`, and pass
   that to the fragment.

   This can be used to write a fragment which executes at most once while
   passing data through:

   ``-ma 'x = y;'``

.. decorator:: callable

   .. option:: --callable, -c

   Call the result of the decorated fragment

.. decorator:: filter

   .. option:: --filter, -f

   Use the decorated fragment as a predicate—only elements for which the
   fragment returns a true value will be passed through.

.. decorator:: many

   .. option:: --many, -m

   Call :func:`spy.many` with the result of the fragment.
