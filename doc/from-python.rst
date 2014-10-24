***************
spy from Python
***************

The :doc:`introduction <intro>` showed how to use spy from the command line.
That's not the only way: spy works just as well from other Python code. The CLI
is just a wrapper around spy's public API to make it easier to get to.

I don't think it is useful in very many cases as a Python library, but if you
want to create an alternative command-line interface for example, this may be of
interest.

:doc:`API documentation <api/index>` is available. What follows is a (very)
brief guide, which I hope to expand on in the future.


Basic usage
-----------

As with the CLI, you create fragments and then pass data through them. And, as
with the CLI, creating fragments is easy. You decorate a regular function with
:func:`spy.fragment`::

   import spy

   @spy.fragment
   def add_five(v):
       return v + 5

So, on to the feeding data part. You don't feed data to fragments on their own,
but to chains, so let's create one::

   chain = spy.chain([add_five])

In order to feed data into it, call the chain object with an iterable to feed
into the chain. The call will return an iterable of the results::

   data = [1, 2, 3, 4]
   print(list(chain(data)))  # [6, 7, 8, 9]

These iterators don't interfere with each other, even if they're created by the
same chain object, so one chain can be used to process multiple independent sets
of input data.


Differences from the CLI
------------------------

As documented, :func:`collect` takes a ``context`` argument. It can be omitted
when using the CLI because it's automatically filled in (it has to be, since
there's no way to access the context object from CLI fragments). There is no
equivalent mechanism outside the CLI, so if you want to use :func:`collect`, you
must provide ``context``. You can get the context object by accepting a
``context`` argument in your fragment function::

   @spy.fragment
   def foo(v, context):
      c = spy.collect(context)
      # do stuff with c
