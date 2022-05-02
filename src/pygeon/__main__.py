import argparse
import os
from pathlib import Path
import json

from pygeon import site_generator


def parse_args():
	parser = argparse.ArgumentParser(
		prog="python -m pygeon",
		description="An opinionated static site generator using the `pygeon` library")
	parser.add_argument("-n","--name",
		help="the name of the website. Defaults to current directory name.")
	parser.add_argument("-pp","--posts_per_page", default=-1, type=int,
		help="number of posts on per page (pagination). "
			"If set to -1 no pagination will be applied.")

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
	navigation_group.add_argument("-can", "--categories_name_in_navigation",
		default="categories", help="the name under which the `categories` page should "
			"appear in the navigation. `None` will exclude it. Default is 'categories'.")
	navigation_group.add_argument("-arn", "--archive_name_in_navigation",
		default="archive", help="the name under which the `archive` page should "
			"appear in the navigation. `None` will exclude it. Default is 'archive'.")
	navigation_group.add_argument("-en", "--exclude_from_navigation",
		default=[], action="extend", nargs="+", type=str,
		help="pages to exclude from navigation, given as a list of "
			"names and/or paths, e.g. ['about','blog/personal']. Default is [].")
	navigation_group.add_argument("-gc", "--do_not_group_categories_in_navigation",
		action="store_const", const=True, default=False,
		help="prevents the categories from being grouped under a 'Category' submenu."
			" Default is `False`.")
	navigation_group.add_argument("-ga", "--do_not_group_archives_in_navigation",
		action="store_const", const=True, default=False,
		help="prevents the archive pages from being grouped under a 'Archive' submenu."
			" Default is `False`.")
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
	category_group.add_argument("-un","--uncategorized_name",
		default="Uncategorized", help="the name for the page containing all"
			" posts which don't have a `category` key in their front matter."
			" Default is 'Uncategorized'.")

	archive_group = parser.add_argument_group("Archive pages",
			"Building an aggregation of posts based on the date they were posted")
	archive_group.add_argument("-ba","--build_archive",
		action="store_const", const=True, default=False,
		help="whether to build archive pages. Defaults to `False`.")
	archive_group.add_argument("-abm","--do_not_archive_by_month",
		action="store_const", const=True, default=False,
		help="whether to prevent buildding an archive by month. Defaults to `False`.")
	archive_group.add_argument("-aby","--do_not_archive_by_year",
		action="store_const", const=True, default=False,
		help="whether to prevent buildding an archive by year. Defaults to `False`.")
	archive_group.add_argument("-amf","--archive_month_format",
		default="%B, %Y",
		help="the `datetime` fomatting to be used for the archive by month."
			" Default is '%%B, %%Y', e.g. 'April, 2022'.")
	archive_group.add_argument("-ayf","--archive_year_format",
		default="%Y",
		help="the `datetime` fomatting to be used for the archive by year."
			" Default is '%%Y', e.g. '2022'.")

	parsed_args = parser.parse_args()

	if parsed_args.name is None:
		parsed_args.name = Path(os.getcwd()).stem

	parsed_args.site_directory = Path(parsed_args.site_directory).absolute()
	for _dir in ["content","theme","templates","static","build"]:
		if getattr(parsed_args, _dir + "_directory") is None:
			setattr(parsed_args, _dir + "_directory", parsed_args.site_directory / _dir)

	return parsed_args


def main(args):
	site_gen = site_generator.SiteGenerator(
		name=args.name,
		content_directory=args.content_directory,
		theme_directory=args.theme_directory,
		templates_directory=args.templates_directory,
		static_directory=args.static_directory,
		build_directory=args.build_directory,
		locally_aggregate_whitelist=args.locally_aggregate_whitelist,
		locally_aggregate_blacklist=args.locally_aggregate_blacklist,
		globally_aggregate_whitelist=args.globally_aggregate_whitelist,
		globally_aggregate_blacklist=args.globally_aggregate_blacklist,
		num_posts_per_page=args.posts_per_page)
	site_gen.process_contentTree()
	site_gen.aggregate_posts()

	if args.build_categories:
		site_gen.build_category_pages(
			allow_uncategorized=not args.do_not_allow_uncategorized,
			uncategorized_name=args.uncategorized_name)

	if args.build_archive:
		site_gen.build_archive(
			args.archive_month_format, args.archive_year_format)
		site_gen.build_archive_pages(
			by_month=not args.do_not_archive_by_month,
			by_year=not args.do_not_archive_by_year)

	if args.custom_navigation is None:
		site_gen.build_navigation(
			extra_filter_func=lambda x: x.name not in args.exclude_from_navigation\
								    and str(x.path) not in args.exclude_from_navigation,
			group_categories=not args.do_not_group_categories_in_navigation,
			group_archive=not args.do_not_group_archives_in_navigation,
			categories_name=args.categories_name_in_navigation,
			archive_name=args.archive_name_in_navigation)

		if args.home_name_in_navigation is not None:
			site_gen.navigation.update({args.home_name_in_navigation: Path("/")})
			site_gen.navigation.move_to_end(args.home_name_in_navigation, last=False)
	else:
		def recursive_parse_paths(_dict):
			return {
				k: (recursive_parse_paths(v) if isinstance(v, dict) else Path(v))\
				for k,v in _dict.items()}

		site_gen.navigation = recursive_parse_paths(json.loads(args.custom_navigation))

	site_gen.render()


if __name__ == "__main__":
	main(parse_args())
