from pathlib import Path


class Config:
    # main
    name = "unnamed"
    url = "http://localhost:8000"
    subtitle = ""
    author_link = ""
    language = "en"
    use_absolute_urls = False
    posts_per_page= -1
    publish_date_key = "publish_date"
    read_date_format = "%d-%m-%Y %H:%M"
    display_date_format = "%B %-d, %Y"
    # directories
    site_directory = "."
    content_directory = None
    theme_directory = None
    static_directory = None
    templates_directory = None
    build_directory = None
    # navigation
    home_name_in_navigation = None
    exclude_categories_from_navigation = False
    exclude_archive_from_navigation = False
    exclude_from_navigation = None
    custom_navigation = None
    # aggregation
    locally_aggregate_whitelist=None
    locally_aggregate_blacklist=None
    globally_aggregate_whitelist=None
    globally_aggregate_blacklist=None
    # category pages
    build_categories = False
    do_not_allow_uncategorized = False
    categories_page_name = ""
    group_categories = False
    uncategorized_name = "Uncategorized"
    # archive pages
    build_archive_by_month = False
    build_archive_by_year = False
    archive_page_name = ""
    group_archive = False
    display_archive_by_month_in_list_page = False
    display_archive_by_year_in_list_page = False
    archive_month_format = "%B, %Y"
    archive_year_format = "%Y"
    # theme
    theme_options = None

    def __init__(self):
        self.exclude_from_navigation = self.exclude_from_navigation or []
        self.locally_aggregate_whitelist = self.locally_aggregate_whitelist or []
        self.locally_aggregate_blacklist = self.locally_aggregate_blacklist or []
        self.globally_aggregate_whitelist = self.globally_aggregate_whitelist or []
        self.globally_aggregate_blacklist = self.globally_aggregate_blacklist or []
        self.theme_options = self.theme_options or {}

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
