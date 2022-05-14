# Notes
- I am not keen on the name `build` for the output folder

# Todos
- make sure all hrefs are stored as str objects
- sort out a nice monochromatic palette for the default theme
- add nested hierarchies to the nav
- look into making the generated site truly static, i.e. not requiring a server
- document the required/supported front matter info for the default theme
- the `build_navigation` currently has a hardcoded bit that creates navigation for everything which needs to be removed when im done
- minify css and js?
- add all the necessary header meta tags to the theme - _the most important are done, it's now a question whether i want to add the specific fb and twitter ones_
- consider rendering the first page of a paginated page to both `{page}/` and `{page}/page{pageNum}`. I know it can be done with a redirect, but I'd rather not require that
- make sure we take care of urlencoding in URLs. tbh, i'd rather just strip/convert all unsupported characters, so URIs are very clear
- properly structure the `__init__.py`
- because im using relative urls, make sure to define a canonical one
- at the moment rebuliding the website deletes the whole `build` folder and recreates it from scratch, which can become quite slow on huge websites, so i need some sort of a smart rebuild.

# Acknowledgements
- I use [Source Sans Pro](https://fonts.google.com/specimen/Source+Sans+Pro) and [Source Serif Pro](https://fonts.google.com/specimen/Source+Serif+Pro) Google fonts for the default theme, under the [SIL Open Font License (OFL)](https://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=OFL).
- [tabler icons](https://tabler-icons.io/) for the default theme
- I used [The excellent lorem ipsum markdown generator by Jasper Van der Jeugt](https://jaspervdj.be/lorem-markdownum/) to generate some example markdown for the unit tests
- One of the custom theme tests is implementing the [Jekyll Hyde theme](https://github.com/poole/hyde)
- One of the custom theme tests is implementing a subste of the [Hugo PaperMod theme](https://github.com/adityatelange/hugo-PaperMod/)
