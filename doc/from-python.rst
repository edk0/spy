***************
spy from Python
***************

The :doc:`introduction <intro>` showed how to use spy from the command line.
That's not the only way: spy works just as well from other Python code. The CLI
is just a wrapper around spy's public API to make it easier to get to.

:doc:`API documentation <api/index>` is available. What follows is a (very) 
brief
guide, which I hope to expand on in the future.

Basic usage
-----------

As with the CLI, you create fragments and then pass data through them. And, as
with the CLI, creating fragments is easy. You decorate a regular function with
:func:`spy.fragment`::

   import spy

   @spy.fragment
   def add_five(v):
       return v + 5

So, on to the feeding data part. :func:`spy.chain` takes a list of fragments and
an initial :term:`iterable` with the data to feed into the chain, and returns an
:term:`iterator` that pulls data out of the other end::

   chain = spy.chain([add_five], [1, 2, 3, 4])

   print(list(chain))  # [6, 7, 8, 9]
