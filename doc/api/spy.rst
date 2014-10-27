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

.. class:: catch()

   A :term:`context manager`. Exceptions raised in the context will be subject
   to spy's traceback formatting and wrapped in a :exc:`CaughtException`.  If
   these are not caught, spy uses an exception hook to force them to be
   formatted properly. If you opt to catch :exc:`CaughtException` instead, you
   can use its :meth:`~CaughtException.print_traceback` method to print the
   formatted traceback without exiting.

.. class:: chain(seq)

   Construct a chain of :term:`fragments <fragment>` from ``seq``.

   :param seq: Fragments to chain together
   :type seq: :term:`sequence`

   .. method:: __call__(data)

      Alias for :meth:`apply`.

   .. method:: apply(data)

      Feed ``data`` into the fragment chain, and return an iterator over the
      resulting data.

   .. classmethod:: auto_fragments(seq)

      Like the regular constructor, but for each element in ``seq``, apply
      :func:`fragment` to it if it isn't already a fragment.

      Items in seq must be either regular functions (not generators) or
      :term:`fragments <fragment>`.

   .. method:: run_to_exhaustion(data)

      Call :meth:`apply`, then iterate until the chain runs out of data.

.. function:: collect(context)

   Return an :term:`iterator` of the elements being processed by the current
   fragment. Can be used to write a fragment that consumes multiple items.

.. decorator:: fragment

   Given a :term:`callable` ``func``, return a :term:`fragment` that calls
   ``func`` to process data. ``func`` must take at least one positional
   argument, a single value to process and return.

   Optionally it can take another argument, called ``context``. If it does, a
   context object will be passed to it on each invocation. This object has no
   documented public functionality; its purpose is to be passed to spy API
   functions that require it (namely :func:`collect`).

.. function:: many(ita)

   Return a signaling object that instructs spy to yield values from ``ita``
   from the current fragment, instead of yielding only one value.
