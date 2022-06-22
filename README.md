# lamya
The `lamya` (_emphasis is on the ya - lamyà_) package provides both an out of the box markdown static site generator and a framework for building your own custom ones.

_I like to think of it as a static site generator generator._

## Install
To install `lamya` you can use pip:

```
pip install lamya[all]
```

The reason I've added the optional `all` dependencies is that by default `lamya` attempts to use `markdown` as a markup processor and `jinja2` as a template engine, but if you know you will be using a different markup processor and template engine you are free to skip the `[all]` and just install `lamya`.

## Quickstart
### CLI
You can run `lamya`'s static site generator as a module to turn a directory of markdown files into a static site:

```
python -m lamya -url "http://my_url.com" --content_directory "path_to_content/" [OPTIONS]
```

This will take all the markdown descendants of the `path_to_content` directory and turn them into a static site, built into a folder called `build` in the current directory.

_NOTE: If no `--content_directory` flag is provided, `./content` will be used. Additionally the `--build_directory` flag can be used to specify where to build the site. For more info about flags have a look at the full [CLI Reference](https://lamya.readthedocs.io/en/latest/cli-reference.html)._

### Build script
Or you could write a simple build script which uses the `lamya.site_generator.SiteGenerator` like so:

```python
from lamya.site_generator import SiteGenerator
from pathlib import Path

site_gen = SiteGenerator(name="dontpanic", url="https://dont.panic",
    subtitle="we demand rigidly defined areas of doubt and uncertainty",
    theme_options={"sidebar":True, "sidebar_image":"/img/sidebar.png"},
    content_directory=Path("content"))

# Make sure all content has been read and any front matter information has been
# extracted, so it can be used in the templates
site_gen.process_content_tree()

# optionally modify your existing content, generate new one, categorize
# posts, etc.

# optionally build a navigation
site_gen.build_navigation()
# or you could manually provide one
# site_gen.navigation = {}

# generate the site
site_gen.render()
```

Alternatively, if you like the idea of mostly maintaining one Config object, which specifies most of your build process, you can utilize the same function that generates the site via the CLI method above - `lamya.site_generator.SiteGenerator.run_from_config()`.

```python
from lamya.config import Config as DefaultConfig
from lamya.site_generator import SiteGenerator

class Config(DefaultConfig):
    name = "dontpanic"
    url = "https://dont.panic"
    subtitle="we demand rigidly defined areas of doubt and uncertainty",
    content_directory="content",
    theme_options = {
        "sidebar": True,
        "sidebar_image": "/img/sidebar.png"
    }

site_gen = SiteGenerator.run_from_config(Config(), render=False)

# We've set `render` to False above, so we can make any changes we'd like
# here before actually rendering the site

# NOTE: That this method is more similar to the CLI method above, since
# all of the functions like `process_content_tree`, `build_navigation`, etc.
# are called inside the `run_from_config`.

site_gen.render()
```

## Features

- designed to be interacted with - import it and build your site the way you want it
- provides an out-of-the-box site generator
- content is described by a simple and easily modified tree structure
- even though, there’s no specific extensions support, lamya is easily extensible, since it’s just a small collection of simple python objects

## Documentation

- [Get started](https://lamya.readthedocs.io/en/latest/get-started.html) - install lamya and learn the basics to hit the ground running
- [Themes](https://lamya.readthedocs.io/en/latest/themes.html) - information about developing, customizing, interacting with themes and also the documentation of the default theme
- [CLI Reference](https://lamya.readthedocs.io/en/latest/cli-reference.html) - command line interface reference
- [API Reference](https://lamya.readthedocs.io/en/latest/api-reference.html) - complete lamya API reference

Or here's a link to the [full documentation](https://lamya.readthedocs.io/en/latest/index.html).

## License
This project is licensed under the [GNU General Public License v3.0](https://github.com/vshotarov/lamya/blob/master/LICENSE)

## Acknowledgements
- [pygments](https://pygments.org/) is used for code highlighting
- [tabler icons](https://tabler-icons.io/) for the default theme
- I used [The excellent lorem ipsum markdown generator by Jasper Van der Jeugt](https://jaspervdj.be/lorem-markdownum/) to generate some example markdown for my tests
