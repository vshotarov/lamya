Custom or No Theme
==================
Building Without a Theme
------------------------
A pygeon website can be generated without the need for a specific theme, as
you can provide your own :ref:`cli-reference:---templates_directory` to source
the jinja2 templates from.

The template that jinja2 uses on all pages is ``default.html``, so as long as
you provide a ``default.html`` inside the specified
:ref:`cli-reference:---templates_directory` your website will build using that
template.

The default value for ``templates_directory`` is just ``templates``, so if you
have a site structure like so::

    my_site_dir/
    └── content/
        └── ...
    └── templates/
        └── default.html
    └── static/
        └── my_stylesheet.css
        └── some_image.png

and you specify that you don't want to source any themes::

    python -m pygeon -url "localhost:8000" --theme_directory "" 

it will have the effect of building a website only using your own custom
templates and static files.

Customizing a Theme by Overwriting Files
----------------------------------------
If you do specify a theme and also have the ``templates`` and ``static``
directories, they will act as overrides for the files inside them that
correspond to files in the theme.

That way we provide a non-destructive way of modifying themes locally.

What that means is that if there's a ``default.html`` file in the theme's
``templates`` directory and you have one in your own ``templates`` directory,
pygeon will pick up your template, but still use the theme's ones for anything
else.

Same goes for the ``static`` directory. Say for example the theme comes with
some default icons, which you would like to overwrite. You can easily do it
by just mimicking the theme's ``static`` directory hierarchy and only adding
the files you would like to overwrite.
