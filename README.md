# Notes
- I am not keen on the name `build` for the output folder
- I really don't like that I use `user_data` as part of the `site_generator`, so then when I create a `RenderablePage` I have to both take information out of the `user_data` and store it in its own separate attributes, but also store the `user_data`. I think the solution would be to just set my attributes on the contentTree instances inside of the site generator.

# Todos
- add support for specifying the `template` in the `SiteGenerator.render` function - i think this might be good the way it is, as i'd rather choose a template from within the template engine, and of course `user_data` can always be used
- consider rendering the first page of a paginated page to both `{page}/` and `{page}/page{pageNum}`. I know it can be done with a redirect, but I'd rather not require that
- make sure we take care of urlencoding in URLs. tbh, i'd rather just strip/convert all unsupported characters, so URIs are very clear
- properly structure the `__init__.py`
- because im using relative urls, make sure to define a canonical one
- at the moment rebuliding the website deletes the whole `build` folder and recreates it from scratch, which can become quite slow on huge websites, so i need some sort of a smart rebuild.

# Acknowledgements
- I used [The excellent lorem ipsum markdown generator by Jasper Van der Jeugt](https://jaspervdj.be/lorem-markdownum/) to generate some example markdown for the unit tests
- One of the custom theme tests is implementing the [Jekyll Hyde theme](https://github.com/poole/hyde)
- One of the custom theme tests is implementing a subste of the [Hugo PaperMod theme](https://github.com/adityatelange/hugo-PaperMod/)
