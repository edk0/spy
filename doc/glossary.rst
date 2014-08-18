********
Glossary
********

.. glossary::

   fragment
      An object which can be used by :func:`spy.chain` to create chained iterators.

      The following kinds of object *only* are considered fragments:

      - The return value of a successful call to :func:`spy.fragment`
      - A generator taking exactly one argument, the iterable to get input
        values from.

      .. note::

         In any given version of spy, it's possible that other objects may work
         as fragments. This is **not part of the API**, and any accidental
         support for using other objects may go away at any time.
