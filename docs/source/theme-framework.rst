Theme framework
===============
Themes define how the content you've written is actually displayed to your readers.

As such a theme is a combination of:

- ``html`` files containing jinja2 template
- ``css`` and ``js`` to complement the html
- any additional static content such as images, other media or any files you might
  want to share

The way to specify what theme you would like to use is by pointing lamya to
where the theme has been placed using the :ref:`cli-reference:---theme_directory`
argument.

If it hasn't been specified, then the default theme would be used. You can
read more about it in the :doc:`default-theme` page.

Customizing the Theme
---------------------
Depending on the theme design philosophy there may be ways of its users
customizing it or providing additional useful information to be displayed in
specific ways.

Those choices can be communicated to the theme in three ways, depending on
which approach for building the website is taken, i.e.  :ref:`build-from-cli`
or :ref:`build-from-script`.

Theme Options as a SiteGenerator argument
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you are building from a script, i.e. importing the
:class:`lamya.site_generator.SiteGenerator`, then you can just provide a
dictionary with all of your theme options to the
:class:`constructor's <lamya.site_generator.SiteGenerator>`
``theme_options`` argument.

.. note::
   What theme options are available is entirely dependent on the theme, so
   lookout for the theme's documentation. Here's the description for the
   :doc:`default theme<default-theme>`.

Theme Options on the CLI
~~~~~~~~~~~~~~~~~~~~~~~~
If you are building from the command line, there are two ways of specifying
the arguments.

The first way is by specifying a ``theme_options`` dictionary in a config file
and then passing that config file to the command line interface using the
:ref:`cli-reference:---from_file` argument.

.. note::
   The config file is not restricted only to theme options and any of the other
   accepted CLI arguments, can also be given in the config file.

The second way of specifying theme options is directly as arguments in the CLI.
Since they can have any arbitrary names, lamya requires the following naming
rules to be met when using this method:

1. flags that represent switches with an implied value, which don't require a
   value being specified should start with the ``-th_`` or ``--theme_option_``
   prefixes, e.g. if a theme provides a dark mode argument and it is False by
   default you can turn it on by saying ``-th_dark_mode`` without any values.

   .. note::
       If you are passing the theme options through a config file, the corresponding
       key to ``-th_dark_mode`` in the ``theme_options`` dictionary would be called
       just ``dark_mode``, as the ``th`` prefixes are only there to provide a clear
       way of specifying theme options on the CLI.

2. key-value type arguments are supported with up to three values corresponding to
   a key. Arguments that accept one value must be prefixed with ``-th1_`` or
   ``--theme_option1``, arguments that accept two values with ``-th2_`` or
   ``--theme_option2`` and arguments accepting three values with ``-th3_`` or
   ``--theme_option3``. E.g.

   ``python -m lamya -url "localhost:8000" -th1_foo bar --theme_option2 foo2 two bars``

3. setting the same argument twice overwrites the previous value, so if a list
   of values is required, use the ``-thl{1/2/3}_`` or ``--theme_option{1/2/3}``
   arguments, like so::

       python -m lamya -url "localhost:8000" \
           -thl2_authors Arthur Dent \
           -thl2_authors Ford Prefect \
           -thl2_authors Tricia McMillan

   which corresponds to the following if given in a config file::

       theme_options = {"authors": [("Arthur","Dent"),("Ford","Prefect"),("Tricia","McMillan")]}

Inside the Template Engine
--------------------------
Once all of the arguments are provided, they are all accessible inside the template
engine using the ``theme_options`` argument on the ``site_info`` struct.

Here's how you might use them inside a jinja2 template:

.. code-block:: django

   <body class="{% if site_info.theme_options.get('dark_mode') %}dark{% endif %}">
       ....
   </body>

Supporting Absolute and Relative URLs
-------------------------------------
lamya registers a jinja2 filter called ``pyg_urlencode`` which does the same
thing as the native jinja2 ``urlencode``, but also makes sure the URL is appended
to the base site URL if the ``use_absolute_urls``
:class:`lamya.site_generator.SiteGenerator` argument is enabled.

What that means is all relative URLs inside templates, should go through the
``pyg_urlencode`` filter to make sure they can safely be converted to absolute
ones if neccessary.
