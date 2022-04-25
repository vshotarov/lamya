# Notes
- I am not keen on the name `build` for the output folder
- The way i handle reading the config file means is not very developer friendly, as then you have no auto completion on the config and site properties

# Todos
- add user data to ContentTree classes?
- implement pagination on the AggregatedPage
- make the automatically build home page an aggregate of all the content on the website by default, but with the support of specifying the content to be aggregated, so it can be limited down to say all the blog posts only
- at the moment rebuliding the website deletes the whole `build` folder and recreates it from scratch, which can become quite slow on huge websites, so i need some sort of a smart rebuild.

# Acknowledgements
- I used [The excellent lorem ipsum markdown generator by Jasper Van der Jeugt](https://jaspervdj.be/lorem-markdownum/) to generate some example markdown for the unit tests
- One of the custom theme tests is implementing the [Jekyll Hyde theme](https://github.com/poole/hyde)
- One of the custom theme tests is implementing a subste of the [Hugo PaperMod theme](https://github.com/adityatelange/hugo-PaperMod/)
