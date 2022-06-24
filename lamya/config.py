"""This module provides a base Config class defining the default parameters
for running a static site generation process, which can be subclassed to overwrite
only the properties you would like."""
from pathlib import Path
from dataclasses import dataclass, field
from typing import Union, List, Dict, Optional


@dataclass
class Config:
    """The base Config class defining the default argument values for a static
    site generation process.

    You will most likely want to overwrite this class to change at least a few
    of the arguments.

    NOTE: The arguments here are the same as those when running from the CLI,
    as this Config is meant to be used to run the whole site generation process,
    rather than just the initialization of the :class:`lamya.site_generator.SiteGenerator`
    class.

    :param name: name of the site
    :param url: url of the site
    :param subtitle: optional subtitle of the site, generally used as a short
        description or motto
    :param author_link: a URL to be placed in the `link rel=author` html tag
    :param language: the language to be placed in the html `lang` property
    :param use_absolute_urls: whether or not to use full absolute URLs instead
        of the default relative ones
    :param posts_per_page: how many posts to have per page. Defaults to -1,
        which means no pagination.
    :param publish_date_key: the key in the front matter to read the publish
        date from
    :param read_date_format: the `datetime` format to expect the publish date in
    :param display_date_format: the `datetime` format to display the publish date in
    :param site_directory: the path to the site folder. If none of the following
        paths - content, theme, etc. are provided they will be folders inside
        this directory by default.
    :param content_directory: the path to the top folder containing the site content
    :param theme_directory: the path to the theme folder
    :param static_directory: the path to a folder containing static files to be
        directly copied over to the `build_directory`
    :param templates_directory: the path to a folder with render templates
    :param build_directory: the path to a folder where to generate the website
    :param home_name_in_navigation: the name under which the home page should
        appear in the navigation
    :param exclude_categories_from_navigation: whether or not to exclude the
        category pages from the navigation if they exist
    :param exclude_archive_from_navigation: whether or not to exclude any
        archive pages from the navigation if they exist
    :param exclude_from_navigation: other :mod:`lamya.content_tree` entities
        to exclude from the navigation specified either by name or path, from the navigation if they exist
    :param exclude_from_navigation: other :mod:`lamya.content_tree` entities
        to exclude from the navigation specified either by name or path
    :param custom_navigation: a custom dict-like object specifying the navigation
    :param locally_aggregate_whitelist: a list of folders that should have their
        children aggregated into their index pages. NOTE: only the whitelist OR
        the blacklist can be specified at a time, but not both.
    :param locally_aggregate_blacklisk: a list of folders that should NOT have their
        children aggregated into their index pages. NOTE: only the whitelist OR
        the blacklist can be specified at a time, but not both.
    :param globally_aggregate_whitelist: a list of pages or posts to aggregate
        into the home page. NOTE: only the whitelist OR
        the blacklist can be specified at a time, but not both.
    :param globally_aggregate_blacklist: a list of pages or posts to NOT aggregate
        into the home page. NOTE: only the whitelist OR
        the blacklist can be specified at a time, but not both.
    :param build_categories: whether to build category pages
    :param do_not_allow_uncategorized: whether to error out if `build_categories`
        is True and there are posts without categories
    :param categories_page_name: the name of the page containing all the posts
        grouped by their categories. If not provided, no such page will be generated.
    :param group_categories: whether to group the category pages into a folder
        rather than generating them directly under the root
    :param uncategorized_name: the name used to display uncategorized posts
    :param build_archive_by_month: whether to build a monthly archive
    :param build_archive_by_yearly: whether to build a yearly archive
    :param archive_page_name: the name of the page containing all the posts
        grouped by their publish dates. If not provided, no such page will be generated.
    :param group_archive: whether to group the archive pages into a folder
        rather than generating them directly under the root
    :param display_by_month_in_list_page: whether to include the monthly archive
        in the `archive_page_name` page
    :param display_by_year_in_list_page: whether to include the yearly archive
        in the `archive_page_name` page
    :param archive_month_format: the `datetime` representation to group the
        the posts by month by
    :param archive_year_format: the `datetime` representation to group the
        the posts by year by
    :param theme_options: a dict-like object containing specific to the theme arguments
    """
    # main
    name: str = "unnamed"
    url: str = "http://localhost:8000"
    subtitle: str = ""
    author_link: str = ""
    language: str = "en"
    use_absolute_urls: bool = False
    posts_per_page: int = -1
    publish_date_key: str = "publish_date"
    read_date_format: str = "%d-%m-%Y %H:%M"
    display_date_format: str = "%B %-d, %Y"
    # directories
    site_directory: Union[str,Path] = "."
    content_directory: Optional[Union[str,Path]] = None
    theme_directory: Optional[Union[str,Path]] = None
    static_directory: Optional[Union[str,Path]] = None
    templates_directory: Optional[Union[str,Path]] = None
    build_directory: Optional[Union[str,Path]] = None
    # navigation
    home_name_in_navigation: Optional[str] = None
    exclude_categories_from_navigation: bool = False
    exclude_archive_from_navigation: bool = False
    exclude_from_navigation: List[str] = field(default_factory=list)
    custom_navigation: Optional[Dict[str, Union[str, Dict]]] = None
    # aggregation
    locally_aggregate_whitelist: List[str] = field(default_factory=list)
    locally_aggregate_blacklist: List[str] = field(default_factory=list)
    globally_aggregate_whitelist: List[str] = field(default_factory=list)
    globally_aggregate_blacklist: List[str] = field(default_factory=list)
    # category pages
    build_categories: bool = False
    do_not_allow_uncategorized: bool = False
    categories_page_name: Optional[str] = None
    group_categories: bool = False
    uncategorized_name: str = "Uncategorized"
    # archive pages
    build_archive_by_month: bool = False
    build_archive_by_year: bool = False
    archive_page_name: Optional[str] = None
    group_archive: bool = False
    display_archive_by_month_in_list_page: bool = False
    display_archive_by_year_in_list_page: bool = False
    archive_month_format: str = "%B, %Y"
    archive_year_format: str = "%Y"
    # theme
    theme_options: Dict = field(default_factory=dict)

    def __post_init__(self):
        self.site_directory = Path(self.site_directory)
        self.content_directory = Path(self.content_directory)\
            if self.content_directory else self.site_directory / "content"
        self.theme_directory = Path(self.theme_directory) if self.theme_directory else None
        self.static_directory = Path(self.static_directory)\
            if self.static_directory else self.site_directory / "static"
        self.templates_directory = Path(self.templates_directory)\
            if self.templates_directory else self.site_directory / "templates"
        self.build_directory = Path(self.build_directory)\
            if self.build_directory else self.site_directory / "build"
