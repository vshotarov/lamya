import argparse
import os
import sys
from pathlib import Path
import json

from lamya import site_generator


class UnrecognizedLamyaArgumentError(Exception):
    pass

class NotEnoughValuesForLamyaArgumentError(Exception):
    pass

class MissingRequiredLamyaArgumentError(Exception):
    pass


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m lamya",
        description="An opinionated static site generator using the `lamya` library",
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-ff","--from_file",
        help="read the arguments from a python file, e.g. "
            "`python -m lamya -ff config.py`. If supplied, all extra command line"
            " arguments will be treated as overrides for the config file.")
    parser.add_argument("-n","--name",
        help="the name of the website. Defaults to current directory name.")
    parser.add_argument("-url","--url")
    parser.add_argument("-st","--subtitle",
        help="the subtitle of the website, usually a short sentence. Defaults to ''.")
    parser.add_argument("-al","--author_link", default="",
        help="author link to be used as a fallback for page/post front matter"
            " author_link key, when specifying the author using the"
            " <link rel='author' ..> tag. Defaults to the ''.")
    parser.add_argument("-l","--language", default="en",
        help="the language of the website as required by the HTML `lang` attribute. "
        "Default is 'en'.")
    parser.add_argument("-uau","--use_absolute_urls",
        action="store_const", const=True, default=False,
        help="whether or not to use absolute URLs. It is only recommended to use"
            " this flag if you'd like to access the website directly from the"
            " filesystem using the 'file://' scheme, rather than serving it.")
    parser.add_argument("-pp","--posts_per_page", default=-1, type=int,
        help="number of posts on per page (pagination). "
            "If set to -1 no pagination will be applied.")
    parser.add_argument("-pdk","--publish_date_key", default="publish_date",
        help="the key used to specify the 'publish_date' in the front matter."
            " Defaults to 'publish_date'.")
    parser.add_argument("-rdf","--read_date_format", default="%d-%m-%Y %H:%M",
        help="the expected date format for reading the 'publish_date' key in the"
            " front matter. Default is %%d-%%m-%%Y %%H:%%M.")
    parser.add_argument("-ddf","--display_date_format", default="%B %-d, %Y",
        help="the format to display the publish date in. Default is %%B %%-d, %%Y.")

    paths_group = parser.add_argument_group("Paths")
    paths_group.add_argument("-sd","--site_directory", default=".",
        help="the path to the site directory. Defaults to the current directory.")
    paths_group.add_argument("-cd","--content_directory",
        help="the path to the content directory of the site."
            " Defaults to `{site_directory}/content`.")
    paths_group.add_argument("-thd","--theme_directory",
        help="the path to the directory of the theme."
            " Defaults to `{site_directory}/theme`.")
    paths_group.add_argument("-td","--templates_directory",
        help="the path to the a directory, containing optional overrides of the"
            " theme's templates. Defaults to `{site_directory}/templates`.")
    paths_group.add_argument("-std","--static_directory",
        help="the path to a directory, containing static files that will directly"
            " be copied over to the `build` directory."
            " Defaults to `{site_directory}/static`.")
    paths_group.add_argument("-bd","--build_directory",
        help="the directory to build the site in."
            " Defaults to `{site_directory}/build`.")

    navigation_group = parser.add_argument_group("Navigation")
    navigation_group.add_argument("-hn", "--home_name_in_navigation",
        help="the name under which the `home` page should "
            "appear in the navigation. `None` will exclude it. Default is `None`.")
    navigation_group.add_argument("-ecn", "--exclude_categories_from_navigation",
        default=False, action="store_const", const=True,
        help="whether to exclude category pages from navigation. Default is False.")
    navigation_group.add_argument("-ean", "--exclude_archive_from_navigation",
        default=False, action="store_const", const=True,
        help="whether to exclude archive pages from navigation. Default is False.")
    navigation_group.add_argument("-en", "--exclude_from_navigation",
        default=[], action="extend", nargs="+", type=str,
        help="pages to exclude from navigation, given as a list of "
            "names and/or paths, e.g. ['about','blog/personal']. Default is [].")
    navigation_group.add_argument("-cn", "--custom_navigation",
        help="accepts a `json` dictionary in the format "
            "{'name1': '/url1', 'name2': {'name2_sub1': '/name2/url_sub2'}, .. }."
            " Default is `None`. If specified will override any automated navigation generation.")

    aggregation_group = parser.add_argument_group("Aggregation",
        "By default, if any folders in the `content_directory` don't have a "
        "defined `index` page, will have an automated one created, which will "
        "be an aggregate of all the posts inside of it (local aggregation)."
        " Additionally, if there's no top-level `index` page defined, it "
        "will be an aggregate of all the posts in the website "
        "(global aggregation). The following options control how both those "
        "aggregators work.")
    aggregation_group.add_argument("-law", "--locally_aggregate_whitelist",
        default=[], action="extend", nargs="+", type=str,
        help="specifies the folder paths or names to aggregate. If nothing is"
            " provided it defaults to aggregating everything.")
    aggregation_group.add_argument("-lab", "--locally_aggregate_blacklist",
        default=[], action="extend", nargs="+", type=str,
        help="specifies the folder paths or names to NOT aggregate. If nothing is"
            " provided it defaults to nothing. NOTE: only the `whitelist` or"
            " the `blacklist` being set is supported, but not both.")
    aggregation_group.add_argument("-gaw", "--globally_aggregate_whitelist",
        default=[], action="extend", nargs="+", type=str,
        help="specifies the folder paths or names to aggregate into the home page."
            " If nothing is provided it defaults to aggregating everything.")
    aggregation_group.add_argument("-gab", "--globally_aggregate_blacklist",
        default=[], action="extend", nargs="+", type=str,
        help="specifies the folder paths or names to NOT aggregate into the home page"
            ". If nothing is provided it defaults to nothing. NOTE: only the "
            "`whitelist` or the `blacklist` being set is supported, but not both.")

    category_group = parser.add_argument_group("Category pages",
        "Building an aggregation of posts per category defined in their front matter.")
    category_group.add_argument("-bc","--build_categories",
        action="store_const", const=True, default=False,
        help="whether or not to build category pages, based on the 'category'"
            " key of their 'front_matter'. Defaults to `False`.")
    category_group.add_argument("-ac","--do_not_allow_uncategorized",
        action="store_const", const=True, default=False,
        help="whether to error if there are uncategorized posts. Defaults to "
            "`False` (not erroring out).")
    category_group.add_argument("-cpn","--categories_page_name", default="",
        help="the name of the `categories` page, which will have a list of all"
            " categories and their posts. If left empty, no such page will be created."
            " Default is ''.")
    category_group.add_argument("-gc","--group_categories",
        action="store_const", const=True, default=False,
        help="whether to group category pages under a folder. The folder name will"
            " be 'categories' if nothing is specified in `categories_page_name`")
    category_group.add_argument("-un","--uncategorized_name",
        default="Uncategorized", help="the name for the page containing all"
            " posts which don't have a `category` key in their front matter."
            " Default is 'Uncategorized'.")

    archive_group = parser.add_argument_group("Archive pages",
            "Building an aggregation of posts based on the date they were posted")
    archive_group.add_argument("-abm","--build_archive_by_month",
        action="store_const", const=True, default=False,
        help="whether to build an archive by month. Defaults to `False`.")
    archive_group.add_argument("-aby","--build_archive_by_year",
        action="store_const", const=True, default=False,
        help="whether to build an archive by year. Defaults to `False`.")
    archive_group.add_argument("-apn", "--archive_page_name", default="",
        help="the name of the `archive` page, which will have a list of all"
            " posts by their month and/or year of publishing. If empty, no"
            " such page will be created. Default is ''.")
    archive_group.add_argument("-ga","--group_archive",
        action="store_const", const=True, default=False,
        help="whether to group archive pages under a folder. The folder name will"
            " be 'archive' if nothing is specified in `archive_page_name`")
    archive_group.add_argument("-damp","--display_archive_by_month_in_list_page",
        action="store_const", const=True, default=False,
        help="whether to display the monthly archive in the archive list page."
            " Default is False.")
    archive_group.add_argument("-dayp","--display_archive_by_year_in_list_page",
        action="store_const", const=True, default=False,
        help="whether to display the yearly archive in the archive list page."
            " Default is False.")
    archive_group.add_argument("-amf","--archive_month_format",
        default="%B, %Y",
        help="the `datetime` fomatting to be used for the archive by month."
            " Default is '%%B, %%Y', e.g. 'April, 2022'.")
    archive_group.add_argument("-ayf","--archive_year_format",
        default="%Y",
        help="the `datetime` fomatting to be used for the archive by year."
            " Default is '%%Y', e.g. '2022'.")

    theme_group = parser.add_argument_group("Theme options",
        "Theme may require different options, such as 'dark' or 'light mode, "
        "including a sidebar or not, social media profile links, etc."
        "Since they may be anything the theme developer is responsible for "
        " outlining what arguments may be set. In order for them to be parsed"
        " correctly the following 3 rules must be considered:\n"
        " \n1. flags with no values start with `-th_` or `--theme_option_`,"
        " e.g. `-th_sidebar`.\n"
        " \n2. we support "
        " key-value pairs with up to three values per key. Simple theme args "
        " must start with `-th1_` or `--theme_option1`, e.g. `-th1_dark_mode` or"
        " `--theme_option1_dark_mode`. Arguments that accept tuples with 2 values"
        " should be prefixed with `-th2_` or `--theme_option2` and the same goes"
        " for arguments that accept tuples with 3 values.\n"
        " \n3. Setting the same"
        " argument twice using `-th1_{arg}` will overwrite the previous value."
        " so if a list of values is required use `-thl1_{arg}`,`-thl2_{arg}`,etc."
        "\n\nNOTE: we only support up to 3 values per key.\n\n"
        "Here are the accepted arguments for the default theme:\n"
        "\n\n    th_breadcrumbs - whether to display breadcrumbs or not. Default is off."
        "\n\n    th_sidebar - whether to build a sidebar or not. Default is off."
        "\n\n    th_sidebar_in_home_only - whether to have the sidebar only on the home page."
        "\n\n    th_sidebar_image_in_home_only - whether to have the sidebar "
        " image only on the home page. Default is off."
        "\n\n    th_sidebar_social_in_home_only - whether to have the sidebar "
        " social icons only on the home page. Default is off."
        "\n\n    th_sidebar_description_in_home_only - whether to have the sidebar "
        " description only on the home page. Default is off."
        "\n\n    th1_sidebar_image - an image for the top of the sidebar, e.g. "
            "`-th1_sidebar_image \"/img/sidebar.png\"`"
        "\n\n    th1_sidebar_image_alt - the alt text for the sidebar image"
        "\n\n    th1_sidebar_description - a bit of descriptive text in the sidebar"
        "\n\n    thl{2/3}_social_links - a list of (name, url, optional img) tuples, e.g."
        "`-thl3_social_links github \"https://github.com/lamya\" \"/img/github.svg\""
        " -thl2_social_links twitter \"https://twitter.com/lamya\"`, which will"
        " produce an icon for github and the text 'twitter' for the twitter link."
        "\n\n    thl{2/3}_links - a list of (name, url, optional nice name) tuples, e.g."
        "`-thl3_links \"my knitting blog\" \"https://knittingforfunandprofit.com\""
        " knittingforfunandprofit.com -thl2_links \"favourite knitting pattern\""
        " \"https://knittingforfunandprofit.com/the-three-crocheters\""
        "\n\n    th_sidebar_archive_nav - whether to include an archive navigation"
        " in the sidebar"
        "\n\n    th_display_archive_by_month_in_sidebar - whether to include"
        " monthly links from the archive in the sidebar. Default is True."
        "\n\n    th_display_archive_by_year_in_sidebar - whether to include"
        " yearly links from the archive in the sidebar. Default is False."
        "\n\n    th1_copyright_year - to be displayed in the footer"
        "\n\n    thl1_extra_css - a number of stylesheets to load after"
        " the theme's ones"
        "\n\n    thl1_extra_js - a number of javascript files to load after"
        " the theme's ones"
        )

    return parser

def parse_args():
    parser = build_parser()

    parsed_args, unknown_args = parser.parse_known_args()

    return parsed_args, unknown_args, {long: short for short,long in\
        [a.option_strings for a in parser._get_optional_actions()]}


def process_args(parsed_args, unknown_args):
    if parsed_args.url is None:
        raise MissingRequiredLamyaArgumentError("The -url, --url argument is required.")

    if parsed_args.name is None:
        parsed_args.name = Path(os.getcwd()).stem

    parsed_args.site_directory = Path(parsed_args.site_directory).absolute()
    for _dir in ["content","templates","static","build"]:
        if getattr(parsed_args, _dir + "_directory") is None:
            setattr(parsed_args, _dir + "_directory", parsed_args.site_directory / _dir)

    # Theme options
    theme_options = {}
    simple_option_prefixes = ["-th1_","-th2_","-th3_","--theme_option1_",
         "--theme_option2_","--theme_option3_"]
    list_option_prefixes = ["-thl1_","-thl2_","-thl3_","--theme_list_option1_",
         "--theme_list_option2_","--theme_list_option3_"]
    while unknown_args:
        current = unknown_args.pop(0)
        is_simple_theme_option = any([current.startswith(x) for x in simple_option_prefixes])
        is_list_theme_option = any([current.startswith(x) for x in list_option_prefixes])

        if current.startswith("-th_") or current.startswith("--theme_option_"):
            theme_options[current.replace("-th_","").replace("--theme_option_","")] = True
            continue

        if not (is_simple_theme_option or is_list_theme_option):
            raise UnrecognizedLamyaArgumentError("Unrecognized argument " + current)

        tuple_size = int(current.split("_")[2 if current.startswith("--") else 0][-1])

        arg_values = []
        for i in range(tuple_size):
            if not unknown_args or unknown_args[0].startswith("-"):
                raise NotEnoughValuesForLamyaArgumentError(
                    "Not enough values for arg " + current)
            arg_values.append(unknown_args.pop(0))

        key = current
        for each in simple_option_prefixes + list_option_prefixes:
            key = key.replace(each,"")

        value = tuple(arg_values) if len(arg_values) > 1 else arg_values[0]

        if is_simple_theme_option:
            theme_options[key] = value
        else:
            if not isinstance(theme_options.get(key,[]), list):
                theme_options[key] = []
            theme_options.setdefault(key,[]).append(value)

    if hasattr(parsed_args,"theme_options"):
        for k,v in theme_options.items():
            parsed_args.theme_options[k] = v
    else:
        parsed_args.theme_options = theme_options

    return parsed_args


if __name__ == "__main__":
    parsed_args,unknown_args,option_strings = parse_args()
    if parsed_args.from_file is None:
        site_generator.SiteGenerator.run_from_config(
            (process_args(parsed_args, unknown_args)))
    else:
        # If we are reading from a file, let's get a dict with all the definitions
        args = {}
        with open(parsed_args.from_file, "r") as f:
            exec(f.read(), {}, args)

        # Then create a simple struct mimicking the parsed_args object
        class ArgsFromFile: pass
        args_object = ArgsFromFile

        # Set all the config info on it
        for k,v in args.items():
            setattr(args_object, k, v)

        # Overwrite any settings if they have been provided via the CLI or
        # if they are missing
        for k,v in parsed_args._get_kwargs():
            if ("--"+k in sys.argv or option_strings["--"+k] in sys.argv)\
                    or not hasattr(args_object, k):
                setattr(args_object, k, v)

        site_generator.SiteGenerator.run_from_config(
            process_args(args_object, unknown_args))
