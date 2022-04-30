# Notes
- I am not keen on the name `build` for the output folder
- I don't like page.user_data["front_matter"], but i also don't want to add the front matter to the contentTree classes, so im leaning towards just defining it on the contentTree instances inside a site generator
- I am starting to reconsider the contentTree not having any content/front_matter as it certainly sounds like it may be useful
- I really don't like that I use `user_data` as part of the `site_generator`, so then when I create a `RenderablePage` I have to both take information out of the `user_data` and store it in its own separate attributes, but also store the `user_data`. I think the solution would be to just set my attributes on the contentTree instances inside of the site generator.

# Todos
- consider rendering the first page of a paginated page to both `{page}/` and `{page}/page{pageNum}`. I know it can be done with a redirect, but I'd rather not require that
- make sure we take care of urlencoding in URLs. tbh, i'd rather just strip/convert all unsupported characters, so URIs are very clear
- rename `group` to `group_by`, as `group` implies actually grouping items into a folder
- properly structure the `__init__.py`
- because im using relative urls, make sure to define a canonical one
- at the moment rebuliding the website deletes the whole `build` folder and recreates it from scratch, which can become quite slow on huge websites, so i need some sort of a smart rebuild.

# Acknowledgements
- I used [The excellent lorem ipsum markdown generator by Jasper Van der Jeugt](https://jaspervdj.be/lorem-markdownum/) to generate some example markdown for the unit tests
- One of the custom theme tests is implementing the [Jekyll Hyde theme](https://github.com/poole/hyde)
- One of the custom theme tests is implementing a subste of the [Hugo PaperMod theme](https://github.com/adityatelange/hugo-PaperMod/)
