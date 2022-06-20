# Notes
- I am not keen on the name `build` for the output folder
- at the moment rebuliding the website deletes the whole `build` folder and recreates it from scratch, which can become quite slow on huge websites, so i need some sort of a smart rebuild.

# Todos
- add support for codehilite and pygment arguments exposed to the user
- make a demo website for the default theme
- add install instructions after this is deployed
- add rss
- properly structure the `__init__.py`

# Acknowledgements
- [pygments](https://pygments.org/) is used for code highlighting
- I use [Source Sans Pro](https://fonts.google.com/specimen/Source+Sans+Pro) and [Source Serif Pro](https://fonts.google.com/specimen/Source+Serif+Pro) Google fonts for the default theme, under the [SIL Open Font License (OFL)](https://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=OFL).
- [tabler icons](https://tabler-icons.io/) for the default theme
- I used [The excellent lorem ipsum markdown generator by Jasper Van der Jeugt](https://jaspervdj.be/lorem-markdownum/) to generate some example markdown for the unit tests
