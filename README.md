# Notes
- I am not keen on the name `build` for the output folder
- Also not very keen on the `index.html` template name, which i use as the template for everything. Maybe `default.html`?
- The way i handle reading the config file means is not very developer friendly, as then you have no auto completion on the config and site properties
- An aggregated page should have a list template, which can also be used for archive, category, search, etc. An elegant way of handling that would be making a get_template_with_fallbacks function
- If you have a super simple blog that literally just has posts, then it would make sense to have those at the top level of your content folder, but my current implementation will treat them as pages
- Storing the site config directly on the site object can cause name clashing, e.g. if i have an archive property on the config but i also want to store data in an archive variable on the class

# Todos
- make the automatically build home page an aggregate of all the content on the website by default, but with the support of specifying the content to be aggregated, so it can be limited down to say all the blog posts only
- at the moment rebuliding the website deletes the whole `build` folder and recreates it from scratch, which can become quite slow on huge websites, so i need some sort of a smart rebuild.
- at the moment the base templates are very opinionated and don't provide anything useful. Let's either remove them or make them even more stripped down

# Done
- Now, if I navigate to a level in the hierarchy, which doesn't have an index file, im presented with a file browser in the web browser, which is definitely not what we want. Do I need to write a 404 page for those instances?
- implement support for adding nested hierarchies into the navigation. Can I just have a nav dict on the config file that specifies that?
- implement pagination

# Acknowledgements
- I used [The excellent lorem ipsum markdown generator by Jasper Van der Jeugt](https://jaspervdj.be/lorem-markdownum/) to generate some example markdown for the unit tests
- One of the custom theme tests is implementing the [Jekyll Hyde theme](https://github.com/poole/hyde)
- One of the custom theme tests is implementing a subste of the [Hugo PaperMod theme](https://github.com/adityatelange/hugo-PaperMod/)
