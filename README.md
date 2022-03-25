# Notes
- I am not keen on the name `build` for the output folder
- I would like to make the code treat all content the same way, i.e. the page containing all the blog posts (presumably `http://url.xyz/blog`) exactly the same as say the about page. So, static individual pages are the same thing as aggregated ones. Writing this makes me feel this is an unnecessary generalization but let's see how it goes.
- The way i handle reading the config file means is not very developer friendly, as then you have no auto completion on the config and site properties
- I make a bit of an assumption, that all top level pages or aggregates are desired to be in the navigation
- Now, if I navigate to a level in the hierarchy, which doesn't have an index file, im presented with a file browser in the web browser, which is definitely not what we want. Do I need to write a 404 page for those instances?

# Todos
- make the automatically build home page an aggregate of all the content on the website by default, but with the support of specifying the content to be aggregated, so it can be limited down to say all the blog posts only
- at the moment rebuliding the website deletes the whole `build` folder and recreates it from scratch, which can become quite slow on huge websites, so i need some sort of a smart rebuild.
- aggregate content properly

# Acknowledgements
- I used [The excellent lorem ipsum markdown generator by Jasper Van der Jeugt](https://jaspervdj.be/lorem-markdownum/) to generate some example markdown for the unit tests
