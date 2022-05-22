Overview
========
The ``pygeon`` package provides both an out of the box markdown static site
generator and a framework for building your own custom ones.

``pygeon`` requires: Python 3.8+.

Quickstart
----------
CLI
~~~
You can run ``pygeon``'s static site generator as a module to turn a directory
of markdown files into a static site::

    python -m pygeon -url "http://my_url.com" --content_directory "path_to_content/" [OPTIONS]

This will take all the markdown descendants of the ``path_to_content`` directory
and turn them into a static site, built into a folder called ``build`` in the
current directory.

.. note::
   If no ``--content_directory`` flag is provided, ``./content`` will be used.
   Additionally the ``--build_directory`` flag can be used to specify where to
   build the site. For more info about flags have a look at the full :doc:`cli-reference`.

Build script
~~~~~~~~~~~~
Or you could write a simple build script which imports the
:class:`pygeon.site_generator.SiteGenerator` like so:

.. code-block:: python

    from pygeon.site_generator import SiteGenerator
    from pathlib import Path

    site_gen = SiteGenerator(name="dontpanic", url="https://dont.panic",
        subtitle="we demand rigidly defined areas of doubt and uncertainty",
        theme_options={"sidebar":True, "sidebar_image":"/img/sidebar.png"},
        content_directory=Path("content"))

    # Make sure all content has been read and any front matter information has been
    # extracted, so it can be used in the templates
    site_gen.process_content_tree()

    # optionally modify your existing content, generate new one, categorize
    # posts, etc.

    # optionally build a navigation
    site_gen.build_navigation()
    # or you could manually provide one
    # site_gen.navigation = {}

    # generate the site
    site_gen.render()

Content Tree only
~~~~~~~~~~~~~~~~~
Lastly, if you have a very specific idea of how you want your site to be built
and would like just a little bit of help managing your content, you can opt
into using only the :mod:`pygeon.content_tree` module and then using it's
features like grouping, filtering, reparenting, etc. to wrangle your content
exactly the way you'd like.

.. code-block:: python

    from pygeon import content_tree
    from pathlib import Path

    ct = content_tree.ContentTree.from_directory(Path("content"))

    # modify your existing content or generate some new one to be added to
    # the content tree 
    #
    # NOTE: have a look at the how-to section for examples

    # render to files using your template engine
    # ...

Features
--------
- designed to be interacted with - import it and build your site the way you want it
- provides an *out-of-the-box* site generator
- content is described by a simple and easily modified tree structure
- even though, there's no specific extensions support, `pygeon` is
  easily extensible, since it's just a small collection of simple python objects

Documentation
-------------
- :doc:`Get started <get-started>` - install pygeon and learn the basics to hit
  the ground running
- :doc:`How-to <how-to>` - guides covering common use cases
- :doc:`CLI Reference <cli-reference>` - command line interface reference
- :doc:`API Reference <api-reference>` - complete pygeon API reference

Bugs/Requests
-------------

License
-------

.. toctree::
   :hidden:
   :includehidden:

   self
   get-started
   how-to
   themes
   cli-reference
   api-reference
