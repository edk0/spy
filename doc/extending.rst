*************
Extending spy
*************

When the ``spy`` command runs, it will import all submodules of the
``spy_plugins`` namespace package. You can extend spy locally or from an
installed package by installing a module there.

Specifically, you should create a directory named ``spy_plugins`` somewhere on
Python's module path (or ship one if you're distributing an installable
package) *without an* ``__init__.py`` containing a Python module that
implements your extension.

There are two primary means of extending spy: adding fragment decorators, and
adding functions to :mod:`~spy.prelude`.


Extending the prelude
=====================

Adding functions to the prelude is trivial: simply import :mod:`spy.prelude` and
put things in it.

.. code-block:: python

   from spy import prelude
   prelude.uc = lambda s: str(s).upper()
   prelude.__all__ += ['uc']

.. code-block:: console

   $ spy -c uc <<< hello
   HELLO


.. _adding-decorators:

Adding decorators
=================

spy's decorators are created using a helper decorator,
:func:`spy.decorators.decorator`, which does a lot of work to set up exception
handling and deal with the optional context argument to fragments. Because of
this, the form decorators must take is slightly prescribed. Basic usage is as
follows:

.. code-block:: python

   @decorator('--uppercase', '-U', doc='Make the result uppercase')
   def uppercase(fn, v, context):
       return str(fn(v, context)).upper()

.. code-block:: console

   $ spy -u pipe <<< hello
   HELLO

In general, the function to which :func:`~spy.decorators.decorator` is applied
to three arguments for the decorated fragment function, the input value and the
context. ``fn`` is adjusted to always take the context argument for simplicity.
The decorator function is responsible for calling ``fn`` and returning the result.

If it's advantageous to do some setup first, it can be pulled into a function
and passed as the ``prep`` keyword argument. Its return value will be passed as
a fourth argument to the decorator.

.. code-block:: python

   def _prep_cached(fn):
       return {}

   @decorator('--cached', '-C', doc='Cache this fragment', prep=_prep_cached)
   def cached(fn, v, context, cache):
       if v not in cache:
           cache[v] = fn(v, context)
       return cache[v]

.. code-block:: console

   $ spy -m '[1,2,2,2,3,4]' -Cc print
   1
   2
   3
   4

Finally, if your decorator should take a literal string rather than a fragment,
use the ``takes_string`` parameter. The decorator API is as above, except that
the fragment function will return a tuple of its execution scope and the string.

.. code-block:: python

   @decorator('--template', '-t', doc='Template this string', takes_string=True)
   def template(fn, v, context):
       env, s = fn(v, context)
       return string.Template(s).substitute(env)

.. code-block:: console

   $ spy '{"a": 10, "b": 20}' -kt '$a $b'
   10 20
