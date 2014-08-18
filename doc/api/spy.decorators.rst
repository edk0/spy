*********************
:mod:`spy.decorators`
*********************

This module contains various function decorators for use in spy fragments.

.. module:: spy.decorators

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

.. decorator:: once

   .. option:: --once, -o

   Run the fragment body at most once; ignore its return value. All data are
   passed through the fragment untouched.
