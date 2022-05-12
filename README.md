# Notes
- I am not keen on the name `build` for the output folder

# Todos
- the `build_navigation` currently has a hardcoded bit that creates navigation for everything which needs to be removed when im done
- consider having an archive list page and potentially a category one
- add fonts licenses both to the theme itself somewhere and on the repo
- add a reference to tabler somewhere in the default theme. powered by?
- replace RuntimeError in `__main__.py` with a custom one
- minify css and js?
- add all the necessary header meta tags to the theme
- consider rendering the first page of a paginated page to both `{page}/` and `{page}/page{pageNum}`. I know it can be done with a redirect, but I'd rather not require that
- make sure we take care of urlencoding in URLs. tbh, i'd rather just strip/convert all unsupported characters, so URIs are very clear
- properly structure the `__init__.py`
- because im using relative urls, make sure to define a canonical one
- at the moment rebuliding the website deletes the whole `build` folder and recreates it from scratch, which can become quite slow on huge websites, so i need some sort of a smart rebuild.

# Acknowledgements
- [tabler icons](https://tabler-icons.io/) for the default theme
- I used [The excellent lorem ipsum markdown generator by Jasper Van der Jeugt](https://jaspervdj.be/lorem-markdownum/) to generate some example markdown for the unit tests
- One of the custom theme tests is implementing the [Jekyll Hyde theme](https://github.com/poole/hyde)
- One of the custom theme tests is implementing a subste of the [Hugo PaperMod theme](https://github.com/adityatelange/hugo-PaperMod/)
