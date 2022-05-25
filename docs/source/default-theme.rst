Default theme
=============
pygeon comes with a simple, mobile friendly and fairly brutalist default theme.

Supported Theme Options
-----------------------

- ``breadcrumbs`` - whether or not to build a breadcrumbs navigation
- ``copyright_year`` - the year to show at the copyright notice in the footer
- ``display_archive_by_month_in_sidebar`` - if ``sidebar_archive_nav`` is turned
  on then this argument specified whether the archive by month should be displayed
  in the sidebar archive navigation
- ``display_archive_by_year_in_sidebar`` - if ``sidebar_archive_nav`` is turned
  on then this argument specified whether the archive by year should be displayed
  in the sidebar archive navigation
- ``extra_css`` - extra ``css`` files to load
- ``extra_js`` - extra ``js`` files to load
- ``links`` - a list of links to display in the sidebar. These can be provided
  either with the ``-thl2_`` or the ``-thl3_`` prefixes, where the first value
  is the link label, the second value is the actual link URL and the third value
  is an optional text to display as the clickable link
- ``sidebar`` - whether to build a sidebar at all
- ``sidebar_archive_nav`` - whether to include archive navigation in the sidebar
- ``sidebar_description`` - a description to show in the sidebar
- ``sidebar_description_in_home_only`` - whether to show the description only
  on the home page
- ``sidebar_image`` - an image to display at the top of the sidebar
- ``sidebar_image_alt`` - the alt text for the sidebar image
- ``sidebar_image_in_home_only`` - whether to display the image only in the home
  page
- ``sidebar_social_in_home_only`` - whther to displace the social links only in
  the home page
- ``social_links`` - a list of social links to display in the sidebar, underneath
  the image. These can be rpvided with either the ``-thl2_`` or the ``-thl3_``
  prefixes, where the first value is the name of the social icon, which if
  there's no image provided will be the clickable text, the second value is
  the actual URL and the third is an optional image to use as an icon
