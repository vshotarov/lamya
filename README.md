# Notes
- I am not keen on the name `build` for the output folder

# Todos
- add support for extra js and maybe css to load
- add a site_info arg with the categories and their pages, so we can link to them from the post metadata
- move publis_date and date format from the FronMatterConfig to the SiteGenerator and add support for specifying different format to read and display
- consider only having the side bar image and description on the home page
- add fonts licenses both to the theme itself somewhere and on the repo
- add a reference to tabler somewhere in the default theme. powered by?
- replace RuntimeError in `__main__.py` with a custom one
- minify css and js?
- add all the necessary header meta tags to the theme
- document the theme and its options
- add support for specifying the `template` in the `SiteGenerator.render` function - i think this might be good the way it is, as i'd rather choose a template from within the template engine, and of course `user_data` can always be used
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
