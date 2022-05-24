Get started
===========
Install pygeon
--------------
``pygeon`` requires Python 3.8+

NOTE: Add install instructions after this is deployed

.. _build-from-cli:

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

.. note::
   For the long list of command line arguments have a look at :doc:`cli-reference`,
   and bear in mind they can all be specified in a config file using the
   :ref:`cli-reference:---from_file` argument.

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

Templates
---------
Additionally, if you would like to make small changes to a theme without
having to fork it and maintain it on your own, the
:ref:`templates directory<cli-reference:--td>` argument is available to
define a folder which will checked for a template's name before reaching
for the template in the theme directory.

What that means is that if the theme you are using uses a template called
``default.html`` and you would like to make a change to that, but leave everything
else the same, then you can write your own ``default.html`` in the
``templates_directory`` which will act as an overwrite.

.. _build-from-script:

Creating more complex websites using build scripts
--------------------------------------------------
The command line way of building websites is certainly sufficient if you are
creating classic personal or blog sites, but if you ever need something more
customizable you are completely free to import the
:class:`SiteGenerator <pygeon.site_generator.SiteGenerator>` and take charge
of how your website is built.

This method implies that you would have a build script of some sort, which
when ran will build your website, but of course can do other things as well,
such as potentially immediately deploying it, maybe letting subscribers know if
there's a new piece of content, maybe as a part of your website you utilize some
scraped content which you can have included in your build script, etc.

The possibilities are literally endless, since you are working with python.

Here's how to get started with using pygeon in that manner.

Say for this example we have an old blog that has multiple authors and the content
is separated as so::

    my_site_dir/
    └── content/
        └── about.md
        └── blog/
            └── arthur_dent
                └── first_blog_post.md
                └── second_blog_post.md
                └── ...
            └── ford_prefect
                └── first_blog_post.md
                └── second_blog_post.md
                └── ...
        └── contact.md

If we just use the CLI build, then none of the author's content will be displayed
in the blog page, as the posts there are not direct descendants. Instead, an
entry for each author would be created in the blog submenu on the navigation.

That's no good for our example.

So, to fix that we can use ``pygeon`` in a build script like so:

.. code-block:: python
   :emphasize-lines: 9,10,11,12,13,14,15,16,17,18,19,20,21,22,23
   :caption: ``my_site_dir/build.py``

   from pygeon.site_generator import SiteGenerator


   site_gen = SiteGenerator(name="Mostly Harmless", url="localhost:8000")

   # read the content from the content directory and put it in a tree structure
   site_gen.process_content_tree()

   ##### IMPORTANT ###############################################################
   # move all author content to be a direct descendant of the blog folder, so it
   # can be displayed in the blog index page, but also store the author information
   # in the user_data dict for each blog post, so it can be used in the template
   #
   # since we call `site_gen.aggregate_posts()` after that, when all the posts
   # ARE direct descendants of the blog folder they will be displayed in its
   # index page
   for author_folder in list(site_gen.content_tree.get("blog").children):
       # NOTE: we copy the children lists, as otherwise we'd be changing them in place
       for child in list(author_folder.children):
           child.parent_to(site_gen.content_tree.get("blog"))
           child.user_data["author"] = author_folder.name

       site_gen.content_tree.get("blog").children.remove(author_folder)

   # aggregate all the content into the home page and all direct descendants into
   # their respective parent index pages
   site_gen.aggregate_posts()

   # build the navigation dict
   site_gen.build_navigation()

   # render into the build directory
   site_gen.render()

What we do in the highlited chunk of code (*everything from the line saying IMPORTANT
to the site_gen.aggregate_posts() line*) is:

- iterate over all direct children of the blog folder, which in our case are the
  two author folders

  - iterate over all children of the current author folder 

    - parent the child (*the actual blog post*) to the blog folder
    - store the author folder name in the ``user_data`` object of that post, so
      it can be accessed in the template engine

  - remove the author folder from the blog folder, so it's not displayed in the
    navigation

Then when we run
:meth:`site_gen.aggregate_posts()<pygeon.site_generator.SiteGenerator.aggregate_posts()>`,
all the blog posts are direct descendants of the blog folder, so they are
aggregated into its index page.

.. note::
   If you remove the highlighted code (*everything from the line saying IMPORTANT
   to the site_gen.aggregate_posts() line*) you will be left with the exact
   same result as if you had ran pygeon through the CLI, since that is exactly
   what we do in the ``__main__.py`` of pygeon.

.. note::
   Also note we're using ``localhost:8000`` as the url argument, since that
   makes it really easy to serve your website via the
   `http.server python module <https://docs.python.org/3/library/http.server.html>`_.

Creating a website, while using the content tree only
-----------------------------------------------------
The last way of using pygeon to create your site, is to only utilize the
:mod:`pygeon.content_tree` module, which is only desirable if you have
incredibly specific and non-standard requirements for your website.

What that means is you will be able to do similar things to what we did above
where we reparented some content, but when it comes to building a navigation
object, categories, archives, etc. and actually rendering the website you are
on your own.

Here's how to get started in those cases:

.. code-block:: python

   import pygeon.content_tree
   from pathlib import Path
   
   
   ct = pygeon.content_tree.ContentTree.from_directory(
       Path("content"), accepted_file_types=[".md"])
   
   # visualise your content tree, to help you decide how to manage it
   print(ct)

   # Root(/) {
   #     PageOrPost(about)
   #     Folder(blog) {
   #         Folder(arthur_dent) {
   #             PageOrPost(first)
   #             PageOrPost(second)
   #       }
   #         Folder(ford_prefect) {
   #             PageOrPost(first)
   #             PageOrPost(second)
   #       }
   #     }
   #     PageOrPost(contact)
   #   }

   # use the ContentTree methods to help you manage your content
   #
   # things like filtering, grouping, reparenting content or flattening hierarchies
   # can be immensely useful for keeping a very clean folder structure, but not
   # having that restrict the actual website
   #
   # additionally the `user_data` dictionaries help pass your data around with
   # your content
   
   # then when you're done, use your render method of choice to actually write
   # the website
