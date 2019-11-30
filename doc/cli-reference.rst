*************
CLI reference
*************

.. contents::


Regular options
===============

.. option:: --break

   Start a post-mortem debugging session with :mod:`pdb` if an exception occurs
   during execution.

.. option:: --each-line, -l

   Process each line as its own string (rather than stdin as a file at once).

   Equivalent to starting with a fragment of ``spy.many(pipe)``, but more
   efficient since we don't need save the contents of the input stream
   for indexing.

.. option:: --no-default-fragments

   Don't add any fragments to the chain that weren't explicitly specified in the
   command line.

.. option:: --no-exception-handling

   Disable spy's exception handling and reformatting. This is mostly only useful
   for debugging changes to spy itself.

.. option:: --pipe-name=<name>

   Name the magic pipe variable ``<name>`` instead of ``pipe``.

.. option:: --prelude=<statement>, -p <statement>

   Run some Python before processing starts.

.. option:: --raw, -r

   Don't wrap :data:`~sys.stdin` before passing it to the first fragment.


Output limiting options
-----------------------

The index arguments for these options refer to results, not input. If a single
piece of input data results in 4 separate pieces of output, they'll all count.

.. option:: --start=<index>, -s <index>

   Start printing results at this zero-based index.

.. option:: --end=<index>, -e <index>

   Stop processing data at this zero-based index.


Decorators
==========

Decorator options must precede a code step. Multiple decorators can stack
together. They have exactly the same effect as decorating a function in Python.

See the decorator :doc:`API docs <api/spy.decorators>` for a list of them.


Alternative actions
===================

.. option:: --help, -h

   Show usage and option descriptions.

.. option:: --show-fragments

   Print out a list of string representations of the complete fragment chain
   that would be executed.
