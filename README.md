# Notes
- I am not keen on the name `build` for the output folder

# Todos
- make sure non aggregated folders have a 404 index page, so we don't ever list the directory
- document `pyg_urlencode` for theme developers
- content styling should be tested more thoroughly, as i hadnt noticed how big margins headlines have
- sort out a nice monochromatic palette for the default theme
- document the required/supported front matter info for the default theme
- add rss
- properly structure the `__init__.py`
- at the moment rebuliding the website deletes the whole `build` folder and recreates it from scratch, which can become quite slow on huge websites, so i need some sort of a smart rebuild.

# Acknowledgements
- I use [Source Sans Pro](https://fonts.google.com/specimen/Source+Sans+Pro) and [Source Serif Pro](https://fonts.google.com/specimen/Source+Serif+Pro) Google fonts for the default theme, under the [SIL Open Font License (OFL)](https://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=OFL).
- [tabler icons](https://tabler-icons.io/) for the default theme
- I used [The excellent lorem ipsum markdown generator by Jasper Van der Jeugt](https://jaspervdj.be/lorem-markdownum/) to generate some example markdown for the unit tests
- One of the custom theme tests is implementing the [Jekyll Hyde theme](https://github.com/poole/hyde)
- One of the custom theme tests is implementing a subste of the [Hugo PaperMod theme](https://github.com/adityatelange/hugo-PaperMod/)
