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

Similarly:

.. code-block:: console

   $ spy -mc reversed < test.txt
   lines
   five
   has
   file
   this


Filter
======

.. code-block:: console

   $ spy -l -fc 'len == 4' < test.txt
   this
   file
   five


Enumerate
=========

Naively:

.. code-block:: console

   $ spy -m "['{}: {}'.format(n, v) for n, v in enumerate(pipe, 1)]" < test.txt
   1: this
   2: file
   3: has
   4: five
   5: lines

Taking advantage of spy piping:

.. code-block:: console

   $ spy -m 'enumerate(pipe, 1)' -i '{}: {}' < test.txt
   1: this
   2: file
   3: has
   4: five
   5: lines

Convert CSV to JSON
===================

.. code-block:: console

   $ spy -c csv.DictReader -c list -c json.dumps < thing.csv > thing.json
