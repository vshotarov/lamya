Get started
===========
Install pygeon
--------------
``pygeon`` requires Python 3.8+

NOTE: Add install instructions after this is deployed

Creating a simple website from the CLI
--------------------------------------
The command line interface is ideal for simple cases like personal websites,
blogs and portfolios.

For those cases the quickest way to get a site up and running is to organize
your content in a directory using the hierarchy you would like to use for
navigation and URLs and run ``pygeon`` from the command line.

Let's consider the following example of a simple personal website::

    my_site_dir/
    └── content/
        └── about.md
        └── blog/
            └── first_blog_post.md
            └── second_blog_post.md
            └── ...
        └── contact.md
        └── index.md

Running ``pygeon`` as a module, while inside the ``my_site_dir`` folder, like so::

    python -m pygeon -url "http://my_url.com" [OPTIONS]

will give us a very simple blank website using the default ``pygeon`` theme.

A couple things to note:

- the ``-url`` is a required flag, as it's necessary for canonical links

- instead of running ``pygeon`` inside the directory, we could also run it from
  anywhere, but give it the :ref:`site_directory<cli-reference:paths>` argument

- we don't have an index page inside the ``blog`` folder, which means that one
  will be automatically generated for it and by default it will be a collection
  of all the posts directly underneath it.

  You can control what posts to aggregate into their respective parent's index
  folders using the local :ref:`cli-reference:aggregation` arguments.

  The global aggregation flags are for aggregating content across the whole
  site into the home index page. That aggregation still happens, even if a
  home index page is defined and is accessible in the template engine for the
  home page as ``page.aggregated_posts``.

  These aggregated lists of posts are sorted by publish date, which is either
  taken from the front matter or if that's not present from the OS last modified
  time.

- the posts - ``first_blog_post.md`` and ``second_blog_post.md`` will not be
  part of the navigation, as by default any nested pages are treated as posts

- if we had another directory inside ``content/blog/`` then that directory would
  have been added to the ``blog`` submenu in the navigation

Content
-------
Let's have a look into what the markdown files would look like.

Markdown
~~~~~~~~
Since the default site generator uses markdown and jinja2 there's no specific
requirements other than complying with python's standard markdown library.

The following markdown extensions are enabled by default:

- footnotes
- tables
- fenced_code
- toc
- `markdown strikethrough <https://github.com/clayrisser/markdown-strikethrough>`_ if installed

Front matter
~~~~~~~~~~~~
Front matter in ``pygeon`` is actual python code that will get executed at build
time and is delimited by lines containing only ``+`` symbols.

Here's an example of a blog post:

.. code-block:: text

    +++
    title = "Life the Universe and Everything"
    publish_date = "01-02-2022 11:42"
    +++
    It is a mistake to think you can solve any major problems just with potatoes.

.. note::
   The date format can be specified using the
   :ref:`--read_date_format<cli-reference:--rdf>` CLI argument or if importing
   the :mod:`pygeon.site_generator` the ``SiteGenerator.read_date_format`` argument.

These are the **only** front matter keys ``pygeon`` understands:

- ``title`` - a string representing the title of the post.

    .. note::
       If it is not provided the title will be intuited to be the name of the
       file with underscores converted to spaces and the first letter of words
       being capitalized.

- ``publish_date`` - a string representing the publish date, which will then
  be interpreted by the ``datetime.strptime`` function, with the format provided
  by the above mentioned ``read_date_format`` arguments

- ``category`` - a string providing a category if category pages will be built

Anything else in the front matter is entirely for the use inside of the template
engine, since the front matter is passed to it as a dictionary containing all of
the information.

Static files
------------
Images, extra stylesheets and javascript files are very common when creating
a website, and as such ``pygeon`` provides an easy way of supporting them.

Both the CLI and the :class:`SiteGenerator <pygeon.site_generator.SiteGenerator>`
accept a ``static_directory`` argument, which specifies a folder, the contents
of which will be directly copied to the ``build`` folder. As such, they will
be directly accessible by their relative URLs.

For example, let's say we've added a profile picture to the website structure
from above::

    my_site_dir/
    └── content/
        └── about.md
        └── blog/
            └── first_blog_post.md
            └── second_blog_post.md
            └── ...
        └── contact.md
        └── index.md
    └── static/
        └── img/
            └── profile.png

Then, anywhere in the website then we can display the profile picture like so::

    <img alt="" src="/img/profile.png">

