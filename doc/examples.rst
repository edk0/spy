********
Examples
********

Sort
====

.. code-block:: console

   $ spy -mc sorted < test.txt
   file
   five
   has
   lines
   this


Filter
======

.. code-block:: console

   $ spy -l -f 'len(pipe) == 4' < test.txt
   this
   file
   five


Enumerate
=========

Naively:

.. code-block:: console

   $ spy -m "['{}: {}'.format(n, v) for n, v in enumerate(pipe, 1)]" < test.txt
   0: this
   1: file
   2: has
   3: five
   4: lines

Taking advantage of spy piping:

.. code-block:: console

   $ spy -m 'enumerate(pipe, 1)' "'{}: {}'.format(*pipe)" < test.txt
   1: this
   2: file
   3: has
   4: five
   5: lines

Convert CSV to JSON
===================

.. code-block:: console

   $ spy -c csv.DictReader -c list -c json.dumps < thing.csv > thing.json
