"""The :mod:`lamya.site_generator` module provides a static site generator, that can
be ran either from the CLI by running `lamya` as a module or by importing
the :class:`lamya.site_generator.SiteGenerator` class and using it in your own scripts.

The static site generator utilises the :mod:`lamya.content_tree` tree implementation
to parse existing content and render it using a template engine (Jinja2 by default),
while optionally aggregating content into list pages, categories and an archive.
"""
from pathlib import Path
import glob
from datetime import datetime
from functools import partial
import os
import shutil
from collections import OrderedDict
import urllib.parse

try:
    import markdown
    try:
        import markdown_strikethrough
    except ImportError:
        markdown_strikethrough = None
except ImportError:
    markdown = None
try:
    import jinja2
except ImportError:
    jinja2 = None

from lamya import content_tree
from lamya import content_processing


class Callbacks: # pylint: disable=too-few-public-methods
    """A struct for specifying callbacks to be run at potential various stages
    of the static site generation process.

    NOTE: At the moment it only contains a callback for immediately after
    :class:`lamya.content_tree.ContentTree` node being created, but I'd like to have
    an easy way of adding more callbacks in the future.
    """
    @staticmethod
    def post_content_tree_entity_create(site_generator, entity):
        """Ran on every single :class:`lamya.content_tree.ContentTree` instance created
        in the context of the site generator.

        :param site_generator: the site generator object
        :param entity: the :class:`lamya.content_tree.ContentTree` instance
        """
        # NOTE: I can use these callbacks to make sure all data that I would
        # like to exist on the content_tree entities actually does, rather
        # than defining everything on the content_tree definitions, which
        # im still not sure is a good/bad idea
        entity.site_generator_data = {
            "is_post": isinstance(entity, content_tree.PageOrPost) and\
                    not site_generator.is_page_func(entity),
            "site_url": site_generator.url}


class RenderablePage: # pylint: disable=too-many-instance-attributes,too-few-public-methods
    """This struct is what will be passed to the template engine, so all the
    properties are seralized into directly usable information.

    :param name: the name of the page or post, as taken directly from the name
        of the file it corresponds to if it hasn't been overwritten
    :param title: falls back to the name with underscores replaced with spaces
        and capital letters at the beginning of the words if a title wasn't
        provided in the front matter
    :param content: the processed markup ready for rendering
    :param href: the relative URL of this page or post
    :param site_url: the URL of the website
    :param aggregated_posts: the list of posts if this is an aggregated page
    :param aggregated_grouped_posts: the `dict` of groups and posts if this
        is an aggregated_grouped_post
    :param pagination: the pagination `dict` if this is a paginated page
    :param publish_date: the publish date as read from the front matter or
        if one wasn't supplied, the last modified time of the source file
    :param user_data: any custom user data that has been supplied
    :param front_matter: the evaluated front matter
    :param is_post: whether ot not this page represents a post or a page
        NOTE: the heuristic for defining this is really naive by default, but the
        `is_page_func` function can be specified on the `SiteGenerator` class
    :param absolute_canonical_href: the canonical url for this page or post
    :param breadcrumbs: the breadcrumbs navigation dict
    """
    def __init__(self, page_or_post):
        """Constructor

        :param page_or_post: the page or post to create a render struct for
        """
        self.name = page_or_post.name
        self.title = page_or_post.front_matter.get(
            "title", self.name.replace("_"," ").title())
        self.content = page_or_post.content
        self.excerpt = content_processing.get_excerpt(self.content) if self.content else ""
        self.href = str(page_or_post.href)
        self.site_url = page_or_post.site_generator_data["site_url"]
        self.aggregated_posts = [] if not isinstance(page_or_post, content_tree.AggregatedPage)\
            else [self.__class__(x) for x in page_or_post.aggregated_posts]
        self.aggregated_grouped_posts = [] if not isinstance(
                page_or_post, content_tree.AggregatedGroupsPage)\
            else {k: [self.__class__(x) for x in v]\
                  for k,v in page_or_post.aggregated_grouped_posts.items()}
        self.pagination = page_or_post.pagination.as_navigation_dict()\
            if hasattr(page_or_post, "pagination")\
                and page_or_post.pagination.max_page_number > 1 else {}
        self.publish_date = page_or_post.site_generator_data.get("publish_date")
        self.user_data = page_or_post.user_data
        self.front_matter = page_or_post.front_matter
        self.is_post = page_or_post.site_generator_data.get("is_post",False)
        self.absolute_canonical_href = urllib.parse.quote_plus(self.site_url + str(
            page_or_post.site_generator_data.get("canonical_href", self.href)))
        self.breadcrumbs = [("home","/")] + [
            (p.name,str(p.href) if isinstance(p, content_tree.Folder) and p.index_page else "")\
                for p in reversed(page_or_post.ancestors[:-1])] +\
            ([(self.title if self.is_post else self.name,self.href)]\
                if (self.href != "/" and not page_or_post.is_index_page()\
                    and self.pagination.get("page_number",1) == 1) else [])


class SiteInfo: # pylint: disable=too-many-instance-attributes,too-few-public-methods
    """This struct represents all the site information to be passed to the
    template engine.

    :param name: the name of the site
    :param url: the url of the site
    :param subtitle: the subtitle of the site, generally used as a short
        description or motto
    :param navigation: the navigation `dict`
    :param lang: the language to specify in the html `lang` property
    :param theme_options: a `dict` with the specified theme options
    :param internal_data: similar to the user data of pages, but specified
        by the site generator
    :param archive_nav: if an archive has been generated, this will be a
        navigation `dict` to all of the archive pages
    :param category_nav: if categories have been generated, this will be a
        navigation `dict` to all of the category pages
    :param display_date_format: the python `datetime` format to display
        the publish dates in
    :param author_link: a link to an author page, to be used in the `meta`
        author tag
    """
    def __init__(self, site_generator):
        """Constructor

        :param site_generator: the `SiteGenerator` object
        """
        self.name = site_generator.name
        self.url = site_generator.url
        self.subtitle = site_generator.subtitle
        self.navigation = site_generator.navigation
        self.lang = site_generator.lang
        self.theme_options = site_generator.theme_options
        self.internal_data = site_generator.internal_data
        self.archive_nav = site_generator.archive.as_navigation_dict() if\
            site_generator.archive else {}
        self.category_nav = site_generator.categories.as_navigation_dict() if\
            site_generator.categories else {}
        self.display_date_format = site_generator.display_date_format
        self.author_link = site_generator.author_link


class SiteGenerator: # pylint: disable=too-many-instance-attributes
    """This class is responsible for generating a static website by aggregating,
    grouping and rendering existing content.

    :param name: name of the site
    :param url: url of the site
    :param subtitle: the subtitle of the site, generally used as a short
        description or motto
    :param content_directory: the path to the top folder containing the site content
    :param theme_directory: the path to the theme folder
    :param static_directory: the path to a folder containing static files to be
        directly copied over into the built website
    :param templates_directory: the path to a folder with templates that will
        overwrite the theme's ones
    :param build_directory: the path to a folder where to generate the website
    :param locally_aggregate_whitelist: a list of folders that should have
        their content aggregated into an index page
    :param locally_aggregate_blacklist: a list of folders that should NOT have
        their content aggregated into an index page
    :param globally_aggregate_whitelist: a list of pages or posts to aggregate
        into the home page
    :param globally_aggregate_blacklist: a list of pages or posts to NOT aggregate
        into the home page
    :param num_posts_per_page: how many posts to have per page
    :param is_page_func: a function that returns True if a piece of content is
        meant to be treated as a static page rather than as a post
    :param front_matter_delimiter: we expect the front matter in the raw content
        of each page/post to be surrounded by lines containing only this character
    :param callbacks: a `Callbacks` struct for running functions at specific times.
        NOTE: at the moment we only run after generating any :mod:`lamya.content_tree` node
    :param lang: the language to put in the `html lang` property
    :param front_matter_publish_date_key: the name of the publish date key
        in the front matter
    :param read_date_format: the `datetime` format to expect the publish date
        in the front matter to be in
    :param display_date_format: the `datetime` format to display the publish date in
    :param author_link: a URL to be placed in the `link rel=author` html tag
    :param theme_options: a `dict` of theme options
    :param use_absolute_urls: whether or not to use full absolute URLs instead
        of the default relative ones
    :param content_tree: the :class:`lamya.content_tree.Root` node that contains the
        content of the static site
    :param internal_data: a `dict` containing extra information about the site
        generation process
    """
    def __init__(self, name, url, subtitle="", content_directory=Path("content"), # pylint: disable=too-many-arguments,too-many-locals
            theme_directory=None, static_directory=Path("static"),
            templates_directory=Path("templates"), build_directory=Path("build"),
            locally_aggregate_whitelist=None, locally_aggregate_blacklist=None,
            globally_aggregate_whitelist=None, globally_aggregate_blacklist=None,
            num_posts_per_page=-1,
            is_page_func=lambda x: isinstance(x.parent, content_tree.Root),
            front_matter_delimiter="+", callbacks=Callbacks(),
            lang="en", front_matter_publish_date_key="publish_date",
            read_date_format="%d-%m-%Y %H:%M", display_date_format="%B %-d, %Y",
            author_link="", theme_options=None, use_absolute_urls=False):
        """Constructor

        :param name: name of the site
        :param url: url of the site
        :param subtitle: optional subtitle of the site, generally used as a short
            description or motto
        :param content_directory: the path to the top folder containing the site content.
            Defaults to a folder called `content` in the current directory. This
            folder is required to exist.
        :param theme_directory: the path to the theme folder. This folder is
            required to exist. If `None` is specified, then the default theme
            will be used. `None` by default.
        :param static_directory: the path to a folder containing static files to be
            directly copied over into the built website. Defaults to a folder
            called `static` in the current directory. This folder is not
            required to exist.
        :param templates_directory: the path to a folder with templates that will
            overwrite the theme's ones. Defaults to a folder called `templates`
            in the current directory. This folder is not required to exist.
        :param build_directory: the path to a folder where to generate the website.
            Defaults to a folder called `build` in the current directory. The
            parent of this folder is required to exist.
        :param locally_aggregate_whitelist: a list of folders that should have
            their content aggregated into an index page. Defaults to []. Either
            the whitelist or the blacklist can be specified, but not both.
        :param locally_aggregate_blacklist: a list of folders that should NOT have
            their content aggregated into an index page. Defaults to []. Either
            the whitelist or the blacklist can be specified, but not both.
        :param globally_aggregate_whitelist: a list of pages or posts to aggregate
            into the home page. Defaults to []. Either the whitelist or the
            blacklist can be specified, but not both.
        :param globally_aggregate_blacklist: a list of pages or posts to NOT aggregate
            into the home page. Defaults to []. Either the whitelist or the
            blacklist can be specified, but not both.
        :param num_posts_per_page: how many posts to have per page. Defaults to
            -1, which means infinitely many posts, i.e. no pagination.
        :param is_page_func: a function that returns True if a piece of content is
            meant to be treated as a static page rather than as a post. Defaults
            to a function checking if the content's parent is the root.
        :param front_matter_delimiter: we expect the front matter in the raw content
            of each page/post to be surrounded by lines containing only this character.
            Defaults to '+'.
        :param callbacks: a `Callbacks` struct for running functions at specific times.
            Defaults to the `Callbacks` struct defined in this module.
        :param lang: the language to put in the `html lang` property. Defaults to 'en'.
        :param front_matter_publish_date_key: the name of the publish date key
            in the front matter. Defaults to `publish_date`.
        :param read_date_format: the `datetime` format to expect the publish date
            in the front matter to be in. Defaults to `%d-%m-%Y %H:%M`.
        :param display_date_format: the `datetime` format to display the publish date in.
            Defaults to `%B %-d, %Y`.
        :param author_link: a URL to be placed in the `link rel=author` html tag.
            Defaults to "".
        :param theme_options: a `dict` of theme options. Defaults to `{}`.
        :param use_absolute_urls: whether or not to use full absolute URLs instead
            of the default relative ones.
        """
        self.name = name
        self.url = url
        self.subtitle = subtitle
        self.content_directory = Path(content_directory)
        self.theme_directory = Path(theme_directory) if theme_directory is not None\
            else Path(__file__).parent / "themes" / "lamya"
        self.static_directory = Path(static_directory)
        self.templates_directory = Path(templates_directory)
        self.build_directory = Path(build_directory)
        self.locally_aggregate_whitelist = locally_aggregate_whitelist or []
        self.locally_aggregate_blacklist = locally_aggregate_blacklist or []
        self.globally_aggregate_whitelist = globally_aggregate_whitelist or []
        self.globally_aggregate_blacklist = globally_aggregate_blacklist or []
        self.num_posts_per_page = num_posts_per_page
        self.is_page_func = is_page_func
        self.front_matter_delimiter = front_matter_delimiter
        self.callbacks = callbacks
        self.lang = lang
        self.front_matter_publish_date_key = front_matter_publish_date_key
        self.read_date_format = read_date_format
        self.display_date_format = display_date_format
        self.author_link = author_link
        self.theme_options = theme_options or {}
        self.use_absolute_urls = use_absolute_urls

        if locally_aggregate_whitelist and locally_aggregate_blacklist:
            raise AggregateError("Both 'locally_aggregate_whitelist' and"
                " 'locally_aggregate_blacklist' have been specified, which is"
                " not supported, as the aggregation strategies is chosen depending"
                " on which one is specified, and if neither is, aggregation is"
                " enabled on everything by default.")

        self.globally_aggregated_posts = None
        self.categories = None
        self.archive = None
        self.navigation = None

        self.content_tree  = content_tree.ContentTree.from_directory(content_directory,
            post_create_callback=partial(callbacks.post_content_tree_entity_create, self))
        self.initialize_renderer()
        self.initialize_markup_processor()

        self.internal_data = {
            "build_date": datetime.now()
        }

    def initialize_renderer(self):
        """This method initializes the template engine which will render the site.

        By default we use `jinja2`, but overwriting this function and the render
        fundtion, should allow other template engines to be used."""
        if jinja2 is None:
            raise NotImplementedError("jinja2 was not found, so it either"
                " needs to be installed or you need to overwrite the"
                " 'initialize_renderer' method on the 'Site' class to use"
                " your own templating engine.")

        self.renderer = Jinja2Renderer([
            str(self.templates_directory),
            str(self.theme_directory / "templates")])
        self.renderer.environment.filters["pyg_urlencode"] = lambda x:\
            ("" if (x.startswith(self.url) or not self.use_absolute_urls) else self.url) +\
                self.renderer.environment.filters["urlencode"](
                    x if (not self.url.startswith("file://") or "." in x.split("/")[-1])\
                        else (x + "/index.html"))

    def initialize_markup_processor(self):
        """This method initializes the function which we will use to process
        the markup into `html`.

        By default we use `markdown`, but overwriting this, should allow other
        markup processors to be used.
        """
        if markdown is None:
            raise NotImplementedError("SiteGenerator requires a"
                " 'markup_processor_func' to be initialized , which is set to"
                " markdown by default, but markdown is not included in the"
                " requirements list, so you need to install it separately.")

        self.markup_processor_func = lambda x:\
            markdown.markdown(x,
                extensions=[
                    "footnotes","tables","fenced_code","toc","codehilite"] +\
                    ([markdown_strikethrough.StrikethroughExtension()]\
                        if markdown_strikethrough else []),
                extension_configs = {
                    "codehilite" : {
                        "linenums": False
                    }
                })

    @staticmethod
    def run_from_config(config, render=True):
        """Use a :class:`lamya.config.Config` object to configure the whole
        generation process, which is all contained in this one function.

        Notably, the only reason to use this instead of providing a file with
        all the parameters to the `--from_file` argument of the `CLI`, is
        to have some other optional custom steps between building the site
        and rendering it.

        :param config: the :class:`lamya.config.Config` object, containing all the arguments
        :param render: whether or not to render the website at the end of the
            function or leave that to the user, so other changes can be made before
            that happens
        :returns: the built :class:`SiteGenerator` object
        """
        site_gen = SiteGenerator(
            name=config.name, url=config.url, subtitle=config.subtitle,
            content_directory=config.content_directory,
            theme_directory=config.theme_directory,
            templates_directory=config.templates_directory,
            static_directory=config.static_directory,
            build_directory=config.build_directory,
            locally_aggregate_whitelist=config.locally_aggregate_whitelist,
            locally_aggregate_blacklist=config.locally_aggregate_blacklist,
            globally_aggregate_whitelist=config.globally_aggregate_whitelist,
            globally_aggregate_blacklist=config.globally_aggregate_blacklist,
            num_posts_per_page=config.posts_per_page, lang=config.language,
            read_date_format=config.read_date_format,
            front_matter_publish_date_key=config.publish_date_key,
            display_date_format=config.display_date_format, author_link=config.author_link,
            theme_options=config.theme_options, use_absolute_urls=config.use_absolute_urls)
        site_gen.process_content_tree()
        site_gen.aggregate_posts()

        if config.build_categories:
            site_gen.build_category_pages(
                allow_uncategorized=not config.do_not_allow_uncategorized,
                uncategorized_name=config.uncategorized_name,
                category_list_page_name=config.categories_page_name,
                group=config.group_categories)

        if config.build_archive_by_month or config.build_archive_by_year:
            site_gen.build_archive(
                config.archive_month_format, config.archive_year_format)
            site_gen.build_archive_pages(
                by_month=config.build_archive_by_month, by_year=config.build_archive_by_year,
                archive_list_page_name=config.archive_page_name, group=config.group_archive,
                display_by_month_in_list_page=config.display_archive_by_month_in_list_page,
                display_by_year_in_list_page=config.display_archive_by_year_in_list_page)

        if config.custom_navigation is None:
            site_gen.build_navigation(
                extra_filter_func=lambda x: x.name not in config.exclude_from_navigation\
                                        and str(x.path) not in config.exclude_from_navigation,
                exclude_categories=config.exclude_categories_from_navigation,
                exclude_archive=config.exclude_archive_from_navigation)

            if config.home_name_in_navigation is not None:
                site_gen.navigation.update({config.home_name_in_navigation: Path("/")})
                site_gen.navigation.move_to_end(config.home_name_in_navigation, last=False)
        else:
            def recursive_parse_paths(_dict):
                return {
                    k: (recursive_parse_paths(v) if isinstance(v, dict) else Path(v))\
                    for k,v in _dict.items()}

            site_gen.navigation = recursive_parse_paths(json.loads(config.custom_navigation))

        if render:
            site_gen.render()

        return site_gen

    def process_content_tree(self):
        """This method goes through all of the content, read from the `content`
        directory and ensures we have all the data we require for them.

        At the moment it only tries to read a `publish_date` for each page.
        """
        ## At this point we have the main hierarchy. Let's now read the source, so
        # we can start optionally grouping the content using different heuristics
        for page in self.content_tree.leaves():
            page.parse_front_matter_and_content()

            # We will be sorting content by date, so let's make sure all content
            # has some sort of a date, either explicit in the front matter or
            # we take the last modified time as a backup
            if page.site_generator_data.setdefault("publish_date", None) is None:
                # Use an `if`, so we can support the user manually setting
                # the publish date beforehand if need be
                last_modified_time = datetime.fromtimestamp(
                    os.path.getmtime(page.source_path) if page.source_path else 0)

                front_matter_publish_date = getattr(page, "front_matter", {}).get(
                    self.front_matter_publish_date_key)
                front_matter_publish_date = datetime.strptime(
                    front_matter_publish_date, self.read_date_format) if\
                    front_matter_publish_date else None

                page.site_generator_data["publish_date"] =\
                    front_matter_publish_date or last_modified_time

                if not page.site_generator_data["publish_date"]:
                    content_tree.warning(f"There's no '{self.front_matter_publish_date_key}'"
                        " key in the front matter for '{page.path}' and neither"
                        " is there a 'source_path' that we can read the last "
                        " modified time from, so the date is going to be 0")

    def aggregate_posts(self):
        """This method uses the aggregation arguments passed to the constructor
        to aggregate posts into index pages.
        """
        ## Aggregate folders with no index pages
        # Check if any folder is missing an index page, which would mean
        # we need to create one. NOTE: most of the time I would imagine this
        # would be the case, as the way I understand using folders is to
        # separate different types of content - blog, archive, portfolio, etc.
        folders_with_no_index = list(filter(
            lambda x: isinstance(x, content_tree.Folder) and x.index_page is None,
            self.content_tree.flat(include_index_pages=False)))

        # Depending on the aggregate whitelists we have different strategies
        to_locally_aggregate = folders_with_no_index

        if self.locally_aggregate_blacklist:
            to_locally_aggregate = [x for x in folders_with_no_index\
                if x.name not in self.locally_aggregate_blacklist and\
                   str(x.path) not in self.locally_aggregate_blacklist]

        if self.locally_aggregate_whitelist:
            to_locally_aggregate = [x for x in folders_with_no_index\
                if x.name in self.locally_aggregate_whitelist or\
                   str(x.path) in self.locally_aggregate_whitelist]

        for folder in to_locally_aggregate:
            folder.index_page = content_tree.AggregatedPage(
                folder.name, sorted(
                    [x for x in folder.children if isinstance(x,content_tree.PageOrPost)],
                    reverse=True, key=lambda x: x.site_generator_data["publish_date"]))
            self.callbacks.post_content_tree_entity_create(self, folder.index_page)
            if self.num_posts_per_page > 0:
                folder.index_page.paginate(self.num_posts_per_page,
                    partial(self.callbacks.post_content_tree_entity_create, self))

        ## Aggregate all posts to optionally be used on the home page
        to_globally_aggregate = list(filter(
            lambda x: not self.is_page_func(x) and\
                      not isinstance(x, content_tree.PaginatedAggregatedPage),
            self.content_tree.leaves(include_index_pages=False)))

        if self.globally_aggregate_blacklist:
            to_globally_aggregate = [x for x in to_globally_aggregate\
                if x.parent and x.parent.name not in self.globally_aggregate_blacklist and\
                   str(x.parent.path) not in self.globally_aggregate_blacklist]

        if self.globally_aggregate_whitelist:
            to_globally_aggregate = [x for x in to_globally_aggregate\
                if x.parent and (x.parent.name in self.globally_aggregate_whitelist or\
                   str(x.parent.path)) in self.globally_aggregate_whitelist]

        # Check if we have a home index page in which case we'll just store
        # the globally aggregated content and if not we'll create an AggregatedPage
        self.globally_aggregated_posts = to_globally_aggregate
        if not self.content_tree.index_page:
            self.content_tree.index_page = content_tree.AggregatedPage(
                "home", sorted(to_globally_aggregate, reverse=True,
                    key=lambda x: x.site_generator_data["publish_date"]))
            self.callbacks.post_content_tree_entity_create(
                    self, self.content_tree.index_page)
            if self.num_posts_per_page > 0:
                self.content_tree.index_page.paginate(self.num_posts_per_page,
                    partial(self.callbacks.post_content_tree_entity_create, self))

    def build_category_pages(self, parent=None, # pylint: disable=too-many-arguments,too-many-locals
            category_accessor= lambda x: getattr(x,"front_matter",{}).get("category",""),
            allow_uncategorized=True, uncategorized_name="Uncategorized",
            leaves_filter= lambda x: True,
            category_list_page_name="categories", group=True):
        """This method reads categories from the content's front matter and
        groups them into category pages.

        :param parent: the :mod:`lamya.content_tree` parent node to put the
            category pages in. If `None` the root will be used.
        :param category_accessor: a function defining how to query the category
            for each page or post node. By default it attempts to read it from
            the `category` key in the front matter.
        :param allow_uncategorized: whether or not to allow some pages or posts
            to be uncategorized or to error out if such pages or posts are found
        :param uncategorized_name: the name of the category to use for posts
            that do not have a category
        :param leaves_filter: an optional function to be used for filtering
            the leaves that should be processed
        :param category_list_page_name: the name to give to the page, containing
            all categories and their posts. If it is falsy, no such page will
            be generated.
        :param group: whether or not to group all category pages under a
            `categories` folder
        """
        grouped = {}
        for p in filter(lambda x: isinstance(x, content_tree.PageOrPost)\
                              and leaves_filter(x)\
                              and not self.is_page_func(x),
                self.content_tree.leaves()):
            grouped.setdefault(category_accessor(p), []).append(p)

        if "" in grouped:
            if not allow_uncategorized:
                raise UncategorizedNotAllowedError("The following pages don't have"
                    " categories, but 'allow_uncategorized' is False " + str(grouped[""]))
            grouped[uncategorized_name] = grouped.pop("")

        for category in grouped:
            grouped[category] = sorted(grouped[category],
                key=lambda x: x.site_generator_data["publish_date"], reverse=True)

        parent = parent or self.content_tree
        category_pages = {}
        all_category_pages = []
        for category, pages in grouped.items():
            aggregated_page = content_tree.AggregatedPage(category or uncategorized_name, pages)
            self.callbacks.post_content_tree_entity_create(self, aggregated_page)
            parent.add_child(aggregated_page)

            if self.num_posts_per_page > 0:
                paginated_pages = aggregated_page.paginate(self.num_posts_per_page,
                    partial(self.callbacks.post_content_tree_entity_create, self))
                category_pages[category] = paginated_pages[0]
                all_category_pages += paginated_pages
            else:
                all_category_pages.append(aggregated_page)
                category_pages[category] = aggregated_page

        categories_folder = None if not group else\
            parent.group((category_list_page_name or "categories"), all_category_pages)

        category_list_page = None
        if category_list_page_name and category_pages:
            category_list_page = content_tree.AggregatedGroupsPage(
                category_list_page_name, grouped)
            self.callbacks.post_content_tree_entity_create(self, category_list_page)
            if categories_folder:
                categories_folder.index_page = category_list_page
            else:
                parent.add_child(category_list_page)

        self.categories = Categories(grouped, category_pages,
            category_list_page, categories_folder, uncategorized_name)

    def build_archive(self, by_month_format="%B, %Y", by_year_format="%Y"):
        """This method builds the `archive` struct, with all the posts in
        their correct groups.

        :param by_month_format: the `datetime` format to use for grouping and
            sorting posts by month
        :param by_year_format: the `datetime` format to use for grouping and
            sorting posts by year

        :returns: the built `Archive` struct
        """
        by_month, by_year = {}, {}
        for post in self.posts():
            by_month.setdefault(post.site_generator_data["publish_date"]\
                .strftime(by_month_format),[]).append(post)
            by_year.setdefault(post.site_generator_data["publish_date"]\
                .strftime(by_year_format),[]).append(post)

        self.archive = Archive(
            OrderedDict(sorted(by_month.items(), reverse=1,
                key=lambda x: datetime.strptime(x[0], by_month_format))),
            OrderedDict(sorted(by_year.items(), reverse=1,
                key=lambda x: datetime.strptime(x[0], by_year_format))))

        return self.archive

    def build_archive_pages(self, parent=None, # pylint: disable=too-many-arguments,too-many-locals
            by_month=True, by_year=False,
            archive_list_page_name="archive", group=True,
            display_by_month_in_list_page=True,
            display_by_year_in_list_page=True):
        """This method takes the previously built `Archive` struct and generates
        the archive pages.

        :param parent: the :mod:`lamya.content_tree` parent node to put the
            archive pages in
        :param by_month: whether or not to write pages for the monthly archive
        :param by_year: whether or not to write pages for the yearly archive
        :param archive_list_page_name: the name to give to the page, containing
            all archive groups and their posts. If false, no such page will be generated.
        :param group: whether or not to group all archive pages under an
            `archives` folder
        :param display_by_month_in_list_page: whether to include the monthly
            archive in the list page
        :param display_by_year_in_list_page: whether to include the yearly archive
            in the list page
        """
        if not hasattr(self, "archive"):
            raise ArchivePagesError(
                "The archive must first be initialized using 'build_archive'"
                " before pages can be made out of it.")

        parent = parent or self.content_tree
        archives = (
            (list(self.archive.posts_by_month.items()) if by_month else []),
            (list(self.archive.posts_by_year.items()) if by_year else []))

        if not (archives[0] or archives[1]):
            raise ArchivePagesError("No posts to put in archive")

        archive_pages = []
        for archive in archives:
            archive_pages.append([])
            for archive_key, posts in archive:
                aggregated_page = content_tree.AggregatedPage(archive_key, posts)
                self.callbacks.post_content_tree_entity_create(self, aggregated_page)
                parent.add_child(aggregated_page)

                if self.num_posts_per_page > 0:
                    archive_pages[-1] +=\
                        aggregated_page.paginate(self.num_posts_per_page,
                            partial(self.callbacks.post_content_tree_entity_create, self))
                else:
                    archive_pages[-1].append(aggregated_page)

        archive_folder = None if not group else\
            parent.group(archive_list_page_name or "archive",
                    archive_pages[0] + archive_pages[1])

        archive_list_page = None
        if archive_list_page_name and (archive_pages[0] or archive_pages[1]) and\
                (display_by_month_in_list_page or display_by_year_in_list_page):
            archive_list = OrderedDict(
                self.archive.posts_by_month if display_by_month_in_list_page else {})
            archive_list.update(
                self.archive.posts_by_year if display_by_year_in_list_page else {})

            archive_list_page = content_tree.AggregatedGroupsPage(
                archive_list_page_name, archive_list)
            self.callbacks.post_content_tree_entity_create(self, archive_list_page)
            if archive_folder:
                archive_folder.index_page = archive_list_page
            else:
                parent.add_child(archive_list_page)

        self.archive.pages_by_month = archive_pages[0]
        self.archive.pages_by_year = archive_pages[1]
        self.archive.list_page = archive_list_page

    def posts(self):
        """Returns all leaves that DO NOT pass the `is_page_func` test."""
        return [x for x in self.content_tree.leaves() if\
                isinstance(x, content_tree.PageOrPost) and not self.is_page_func(x)]

    def build_navigation(self, filter_func=None, extra_filter_func=None,
            exclude_categories=False, exclude_archive=False):
        """Builds a navigation structure.

        :param filter_func: a function to filter out pages from the navigation.
            If `None` a default function will be used, which boils down to adding
            pages to the navigation if any of the following are true:

            - the node passes the `is_page_func` or it is a
                :class:`lamya.content_tree.Folder`
            - the node is an `index_page`
            - the node is a `category` page and categories are not excluded
            - the node is an `archive` page and the archive is not excluded

            AND BOTH of the following are true:

            - this node is not the home page
            - if this node is part of a pagination, it is the first page, otherwise
                assume `True`
        :param extra_filter_func: a second filtering function, so if a bit of
            extra filtering is required on top of the default function it can
            easily be provided
        :param exclude_categories: whether or not to exclude any category pages
            from the navigation
        :param exclude_archive: whether or not to exclude any archive pages
            from the navigation
        """
        if self.navigation:
            content_tree.warning("Navigation already exists, overwriting..")

        extra_filter_func = extra_filter_func or (lambda _: True)
        is_category_page_func = lambda x: False if not self.categories\
            else x.path in [p.path for p in list(self.categories.all_pages) +\
                ([self.categories.list_page] if self.categories.list_page else [])]
        is_archive_page_func = lambda x: False if not self.archive\
            else x.path in [p.path for p in self.archive.all_pages +\
                ([self.archive.list_page] if self.archive.list_page else [])]

        filter_func = filter_func or (lambda x:\
               (((isinstance(x, content_tree.AbstractPageOrPost) and self.is_page_func(x))\
                    and not is_category_page_func(x) and not is_archive_page_func(x))\
                or isinstance(x, content_tree.Folder)\
                or (isinstance(x, content_tree.AbstractPageOrPost) and x.is_index_page())\
                or (not exclude_categories and is_category_page_func(x))\
                or (not exclude_archive and is_archive_page_func(x)))\
            and x != self.content_tree.index_page and\
            (x.pagination.page_number == 1 if hasattr(x, "pagination") else True))

        navigatable_tree = self.content_tree.filter(
            lambda x: (filter_func(x) if filter_func else True)\
                      and (extra_filter_func(x) if extra_filter_func else True), True)
        self.navigation = navigatable_tree.as_dict(
            lambda x: str(x.href),
            lambda x: str(x.href)\
                if isinstance(x, content_tree.Folder) and x.index_page else None)

    def render(self,
            to_renderable_page=RenderablePage, to_site_info=SiteInfo,
            markup_processor_func=None,
            template_accessor_func=lambda x: x.front_matter.get("template","default.html"),
            **kwargs):
        """This method renders the site into the build folder.

        :param to_renderable_page: a function that converts an `AbstractPageOrPost`
            into a struct containing the information necessary for rendering that
            page or post. That struct is then passed to the template engine.
            Default is `RenderablePage`.
        :param to_site_info: a function that converts the `SiteGenerator`
            into a struct containing the information necessary for the template.
            Default is `SiteInfo`.
        :param markup_processor_func: an optional markup processing function.
            If `None` the `markup_processor_func` property of the class will
            be used. Default is `None`.
        :param template_accessor_func: a function specifying how to choose a
            template for each leaf node. Defaults to checking if there's a
            'template' argument in the front matter and if not uses 'default.html'.
        :param kwargs: any other optional information to pass to the template engine
        """
        if markup_processor_func is None:
            markup_processor_func = self.markup_processor_func

        if self.build_directory.exists():
            shutil.rmtree(self.build_directory)

        self.build_directory.mkdir()

        # Copy over static content
        def copy_static(static_dir):
            if static_dir.exists():
                for x in glob.glob(str(static_dir) + "/**/*", recursive=True):
                    p = Path(x)
                    if not p.is_file():
                        continue

                    destination = self.build_directory / p.relative_to(static_dir)
                    if not destination.parent.exists():
                        os.makedirs(destination.parent)

                    shutil.copy2(x,destination)

        copy_static(self.theme_directory / "static")
        copy_static(self.static_directory)

        # We want to render aggregated pages last, so we make sure that all
        # posts that they aggregate already have their content processed
        for leaf in sorted(self.content_tree.leaves(),
                key=lambda x: len(getattr(x, "aggregated_posts", []) +\
                                  list(getattr(x, "aggregated_grouped_posts", {}).keys()))):
            # Make sure the content has been read and processed
            if leaf._content is None or leaf._front_matter is None:
                leaf.parse_front_matter_and_content()
                leaf.process_content(markup_processor_func)

            # We may need to write the same page to multiple paths, because
            # of pagination, so we store the path in a list
            paths = [leaf.render_path(self.build_directory)]

            # Let's write the first page of each pagination both to the
            # respective '/' and '/page1' URLs, as it's a bit awkward otherwise.
            if isinstance(leaf, content_tree.PaginatedAggregatedPage)\
                    and leaf.pagination.page_number == 1\
                    and leaf.pagination.max_page_number != 1:
                # If it's already the index page, let's also write it to /page1
                if leaf == getattr(leaf.parent, "index_page", None):
                    paths.append(paths[0].parent / "page1" / "index.html")
                else:
                    # Otherwise, we need to write to the index page
                    paths.append(paths[0].parent.parent / "index.html")
                    # Make sure we consistently use '/' as the canonical URL
                    leaf.site_generator_data["canonical_href"] =\
                        (leaf.parent.href / leaf.name) if leaf.parent else ""

            for path in paths:
                if not path.parent.exists():
                    os.makedirs(path.parent)

                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.renderer.render(template_accessor_func(leaf),
                        page=to_renderable_page(leaf),
                        site_info=to_site_info(self), **kwargs))

        # Make sure we don't have folders with no index files in them, which
        # would show a file browser in the web browser
        class _404Page: # pylint: disable=too-few-public-methods
            front_matter = {}
        for folder in filter(lambda x: isinstance(x, content_tree.Folder),
                self.content_tree.flat(False) + [self.content_tree]):
            if not folder.index_page:
                if not folder.leaves():
                    continue
                folder_render_path = self.build_directory /\
                    folder.path.relative_to("/") / "index.html"
                if not folder_render_path.parent.exists():
                    os.makedirs(folder_render_path.parent)

                with open(folder_render_path, "w",
                        encoding="utf-8") as f:
                    f.write(self.renderer.render("404.html",
                        page=_404Page(),
                        site_info=to_site_info(self)))

                if folder == self.content_tree:
                    content_tree.warning(
                        "There's no home index page. Consider writing a custom"
                        " one or calling the `SiteGenerator.aggregate_posts method`.")


class Jinja2Renderer: # pylint: disable=too-few-public-methods
    """A thin wrapper around the jinja2 environment to provide a framework
    for using different renderers.

    :param environment: the `jinja2` environment
    """
    def __init__(self, template_directories):
        """Constructor

        :param template_directories: a number of paths to look for templates in
        """
        self.environment = jinja2.Environment(
            loader=jinja2.ChoiceLoader(
                [jinja2.FileSystemLoader(x) for x in template_directories]),
            autoescape=jinja2.select_autoescape(),
            trim_blocks=True, lstrip_blocks=True)

    def render(self, template, **render_data):
        """Renders the given template, with the passed in render date.

        :param template: the `template` to use for rendering
        :param render_data: any data to be passed to the template engine
        """
        return self.environment.get_template(template).render(**render_data)


class Categories: # pylint: disable=too-many-arguments
    """A struct grouping all the relevant categories information.

    :param posts_by_category: a `dict` containing all the posts belonging
        to specific categories
    :param pages_by_category: a `dict` mapping a category name to the category page
    :param list_page: the optional page containing all categories and their posts
        that may have been built
    :param folder: an optional folder if the categories have been grouped
    :param uncategorized_name: the name of the uncategorized category
    """
    def __init__(self, posts_by_category, pages_by_category, list_page, folder,
            uncategorized_name):
        """Constructor

        :param posts_by_category: a `dict` containing all the posts belonging
            to specific categories
        :param pages_by_category: a `dict` mapping a category name to the category page
        :param list_page: the optional page containing all categories and their posts
            that may have been built
        :param folder: an optional folder if the categories have been grouped
        :param uncategorized_name: the name of the uncategorized category
        """
        self.posts_by_category = posts_by_category
        self.pages_by_category = pages_by_category
        self.list_page = list_page
        self.folder = folder
        self.uncategorized_name = uncategorized_name

    @property
    def all_pages(self):
        """This method returns all category pages, except for the list page."""
        return self.pages_by_category.values()

    def as_navigation_dict(self):
        """This method maps the categories structure into a simple `dict`,
        so it can be accessed in the template engine.
        """
        return {
            "self": getattr(self.list_page, "href", None),
            "categories": {k: str(v.href) for k,v in self.pages_by_category.items()},
            "uncategorized_name": self.uncategorized_name }


class Archive:
    """A struct grouping all of the relevant archives information.

    :param posts_by_month: the posts grouped into a mapping by month
    :param posts_by_year: the posts grouped into a mapping by year
    :param pages_by_month: the pages grouped into a mapping by month
    :param pages_by_year: the pages grouped into a mapping by year
    :param list_page: the optional page containing all archives and their posts
    """
    def __init__(self, posts_by_month, posts_by_year):
        """Constructor

        :param posts_by_month: the posts grouped into a mapping by month
        :param posts_by_year: the posts grouped into a mapping by year
        :param pages_by_month: the pages grouped into a mapping by month
        :param pages_by_year: the pages grouped into a mapping by year
        :param list_page: the optional page containing all archives and their posts
        """
        self.posts_by_month = posts_by_month
        self.posts_by_year = posts_by_year
        self.pages_by_month = []
        self.pages_by_year = []
        self.list_page = None

    @property
    def all_pages(self):
        """This property returns all pages by month and year."""
        return self.pages_by_month + self.pages_by_year

    def as_navigation_dict(self):
        """This method returns a simple `dict` containing all the archive posts
        and pages information, so it can be easily accessed in the template engine.
        """
        return {
            "by_month": [(p.name, str(p.href)) for p in self.pages_by_month\
                if not hasattr(p, "pagination") or p.pagination.page_number == 1],
            "by_year": [(p.name, str(p.href)) for p in self.pages_by_year\
                if not hasattr(p, "pagination") or p.pagination.page_number == 1]
            }


class AggregateError(Exception):
    """Raised when attempting to use both a whitelist and a blacklist for
    specifying content to be aggregated."""

class UncategorizedNotAllowedError(Exception):
    """Raised when a category is required, but none has been specified."""

class ArchivePagesError(Exception):
    """Raised when an attempt is made to create the archive pages, before the
    content has been created or when there's nothing to archive."""
