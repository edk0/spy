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


Try Except
==========

If there is a lot of data with a few inconsistent records ``--try/-t`` will filter
out these records.

.. code-block:: console

   $ cat > books.json <<EOF
   [
       {"title": "A book", "author": "Alfred Someone"},
       {"title": "Something else", "author": "Writer"},
       {"tilt": "No idea", "author": "Mike Other"}
   ]
   EOF

   $ cat books.json | spy -mc json.load -o author 'pipe.split()' \
       -tk 'f"Firstname: {author[0]}\nLastname: {author[1]}\nTitle: {title}"'
   Firstname: Alfred
   Lastname: Someone
   Title: A book
