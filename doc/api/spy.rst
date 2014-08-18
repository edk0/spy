**********
:mod:`spy`
**********

This module exposes spy's core API.

.. seealso::

   :mod:`spy.decorators`
       Function :term:`decorators <decorator>` for use with spy fragments

.. module:: spy

Constants
---------

.. data:: DROP

   A signaling object: when returned from a :term:`fragment`, the fragment will
   not yield any value.


Exceptions
----------

.. exception:: CaughtException

   .. method:: print_traceback()

      Print the (formatted) traceback captured when the exception was raised.


Functions
---------

.. class:: catch(exit=True)

   A :term:`context manager`. Exceptions raised in the context will be subject
   to spy's traceback formatting.

   If ``exit`` is true, the traceback will be printed and :exc:`SystemExit` will
   be raised. Otherwise, a :exc:`CaughtException` will be raised—you can use its
   :meth:`~CaughtException.print_traceback` method to print the traceback.

.. class:: chain(seq, init=[None])

   Construct a chain of :term:`fragments <fragment>` from ``seq``. When
   iterated, yield values from the right-hand end of the chain.

   :param seq: Fragments to chain together
   :type seq: :term:`sequence`
   :param init: Input with which to feed the first fragment
   :type init: :term:`iterable`

   .. method:: run_to_exhaustion()

      Iterate until the chain runs out of data.

   .. classmethod:: with_defaults(seq, \*, stream=None, \*\*kwargs)

      Like the standard constructor, but with useful fragments inserted at
      either end of ``seq``. If ``stream`` is specified, this includes a
      fragment which yields a file-like object wrapping the given stream.

.. function:: collect()

   Return an :term:`iterator` of the elements being processed by the current
   fragment. Can be used to write a fragment that consumes multiple items.

.. decorator:: fragment

   Given a :term:`callable` ``func``, return a :term:`fragment` that calls
   ``func`` to process data. ``func`` must take one positional argument.

.. function:: many(ita)

   Return a signaling object that instructs spy to yield values from ``ita``
   from the current fragment, instead of yielding only one value.
