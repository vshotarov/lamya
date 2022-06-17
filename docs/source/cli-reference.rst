CLI Reference
=============

.. toctree::
   :hidden:

   Site options <self>

.. sphinx_argparse_cli::
   :module: pygeon.__main__
   :func: build_parser
   :prog: 
   :title:

.. _cli_reference_theme-options:

Theme options
-------------

Theme may require different options, such as 'dark' or 'light mode, including a sidebar or not, social media profile links, etc. Since they may be anything the theme developer is responsible for outlining what arguments may be set.

In order for them to be parsed correctly the following 3 rules must be considered:

1. flags with no values start with ``-th_`` or ``--theme_option_``, e.g. ``-th_sidebar``.

2. we support  key-value pairs with up to three values per key. Simple theme args  must start with ``-th1_`` or ``--theme1_option``, e.g. ``-th1_dark_mode`` or ``--theme_option1_dark_mode``. Arguments that accept tuples with 2 values should be prefixed with ``-th2_`` or ``--theme_option2`` and the same goes for arguments that accept tuples with 3 values.

3. Setting the same argument twice using ``-th1_{arg}`` will overwrite the previous value. so if a list of values is required use ``-thl1_{arg}``,``-thl2_{arg}``,etc.

NOTE: we only support up to 3 values per key.

Here are the accepted arguments for the default theme:


  - **th_breadcrumbs** - whether to display breadcrumbs or not. Default is off.

  - **th_sidebar** - whether to build a sidebar or not. Default is off.

  - **th_sidebar_in_home_only** - whether to build the sidebar only on the home page. Default is off.

  - **th_sidebar_image_in_home_only** - whether to have the sidebar  image only on the home page. Default is off.

  - **th_sidebar_social_in_home_only** - whether to have the sidebar  social icons only on the home page. Default is off.

  - **th_sidebar_description_in_home_only** - whether to have the sidebar  description only on the home page. Default is off.

  - **th1_sidebar_image** - an image for the top of the sidebar, e.g.

    ``-th1_sidebar_image "/img/sidebar.png"``

  - **th1_sidebar_image_alt** - the alt text for the sidebar image

  - **th1_sidebar_description** - a bit of descriptive text in the sidebar

  - **thl{2/3}_social_links** - a list of (name, url, optional img) tuples, e.g.

    ``-thl3_social_links github "https://github.com/pygeon" "/img/github.svg" -thl2_social_links twitter "https://twitter.com/pygeon"``,
    
    which will produce an icon for github and the text 'twitter' for the twitter link.

  - **thl{2/3}_links** - a list of (name, url, optional nice name) tuples, e.g.

    ``-thl3_links "my knitting blog" "https://knittingforfunandprofit.com" knittingforfunandprofit.com -thl2_links "favourite knitting pattern" "https://knittingforfunandprofit.com/the-three-crocheters"``

  - **th_sidebar_archive_nav** - whether to include an archive navigation in the sidebar

  - **th_display_archive_by_month_in_sidebar** - whether to include monthly links from the archive in the sidebar. Default is True.

  - **th_display_archive_by_year_in_sidebar** - whether to include yearly links from the archive in the sidebar. Default is False.

  - **th1_copyright_year** - to be displayed in the footer

  - **thl1_extra_css** - a number of stylesheets to load after the theme's ones

  - **thl1_extra_js** - a number of javascript files to load after the theme's ones

