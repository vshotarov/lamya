from pathlib import Path
from datetime import datetime
from functools import partial
import os
import shutil
from collections import OrderedDict

try:
	import markdown
except ImportError:
	markdown = None
try:
	import jinja2
except ImportError:
	jinja2 = None

from pygeon import contentTree
from pygeon import contentProcessing


class AggregateError(Exception):
	pass

class UncategorizedNotAllowedError(Exception):
	pass

class MarkupProcessorError(Exception):
	pass

class ArchivePagesError(Exception):
	pass

class NavigationError(Exception):
	pass


class FrontMatterConfig:
	key_publish_date = "publish_date"
	date_format = "%d-%m-%Y %H:%M"


class Callbacks:
	@staticmethod
	def post_contentTree_entity_create(siteGenerator, entity):
		# NOTE: I can use these callbacks to make sure all data that I would
		# like to exist on the contentTree entities actually does, rather
		# than defining everything on the contentTree definitions, which
		# im still not sure is a good/bad idea
		entity.site_generator_data = {}


class RenderablePage:
	def __init__(self, pageOrPost):
		self.name = pageOrPost.name
		self.title = self.name.replace("_"," ").title()
		self.content = pageOrPost.content
		self.excerpt = contentProcessing.get_excerpt(self.content)
		self.href = pageOrPost.href
		self.aggregated_posts = [] if not isinstance(pageOrPost, contentTree.AggregatedPage)\
			else [RenderablePage(x) for x in pageOrPost.aggregated_posts]
		self.pagination = pageOrPost.pagination.as_navigation_dict()\
			if hasattr(pageOrPost, "pagination") else {}
		self.publish_date = pageOrPost.site_generator_data.get("publish_date")
		self.user_data = pageOrPost.user_data
		self.front_matter = pageOrPost.front_matter


class SiteInfo:
	def __init__(self, site_generator):
		self.name = site_generator.name
		self.navigation = site_generator.navigation


class SiteGenerator:
	def __init__(self, name, content_directory="content", theme_directory="theme",
			static_directory="static", templates_directory="templates",
			build_directory="build", locally_aggregate_whitelist=[],
			locally_aggregate_blacklist=[], globally_aggregate_whitelist=[],
			globally_aggregate_blacklist=[], num_posts_per_page=1,
			is_page_func=lambda x: isinstance(x.parent, contentTree.Root),
			front_matter_delimiter="+", callbacks=Callbacks()):
		self.name = name
		self.content_directory = Path(content_directory)
		self.theme_directory = Path(theme_directory)
		self.static_directory = Path(static_directory)
		self.templates_directory = Path(templates_directory)
		self.build_directory = Path(build_directory)
		self.locally_aggregate_whitelist = locally_aggregate_whitelist
		self.locally_aggregate_blacklist = locally_aggregate_blacklist
		self.globally_aggregate_whitelist = globally_aggregate_whitelist
		self.globally_aggregate_blacklist = globally_aggregate_blacklist
		self.num_posts_per_page = num_posts_per_page
		self.is_page_func = is_page_func
		self.front_matter_delimiter = front_matter_delimiter
		self.callbacks = callbacks

		if locally_aggregate_whitelist and locally_aggregate_blacklist:
			raise AggregateError("Both 'locally_aggregate_whitelist' and"
				" 'locally_aggregate_blacklist' have been specified, which is"
				" not supported, as the aggregation strategies is chosen depending"
				" on which one is specified, and if neither is, aggregation is"
				" enabled on everything by default.")

		self.title_formatting = self.name + " | {page.title}"
		self.contentTree  = contentTree.ContentTree.from_directory(content_directory,
			post_create_callback=partial(callbacks.post_contentTree_entity_create, self))
		self.initialize_renderer()
		self.initialize_markup_processor()

	def initialize_renderer(self):
		if jinja2 is None:
			raise NotImplementedError("jinja2 was not found, so it either"
				" needs to be installed or you need to overwrite the"
				" 'initialize_renderer' method on the 'Site' class to use"
				" your own templating engine.")

		self.renderer = Jinja2Renderer([
			self.templates_directory, self.theme_directory / "templates"])

	def initialize_markup_processor(self):
		if markdown is None:
			raise NotImplementedError("SiteGenerator requires a"
				" 'markup_processor_func' to be initialized , which is set to"
				" markdown by default, but markdown is not included in the"
				" requirements list, so you need to install it separately.")

		self.markup_processor_func = markdown.markdown

	def process_contentTree(self):
		## At this point we have the main hierarchy. Let's now read the source, so
		# we can start optionally grouping the content using different heuristics
		for page in self.contentTree.leaves():
			page.parse_front_matter_and_content()

			# We will be sorting content by date, so let's make sure all content
			# has some sort of a date, either explicit in the front matter or
			# we take the last modified time as a backup
			if page.site_generator_data.setdefault("publish_date", None) is None:
				# Use an `if`, so we can support the user manually setting
				# the publish date beforehand if need be
				last_modified_time = datetime.fromtimestamp(
					os.path.getmtime(page.source_path) if page.source_path else 0)

				front_matter_publish_date = page.front_matter.get(
					FrontMatterConfig.key_publish_date)
				front_matter_publish_date = datetime.strptime(
					front_matter_publish_date, FrontMatterConfig.date_format) if\
					front_matter_publish_date else None

				page.site_generator_data["publish_date"] =\
					front_matter_publish_date or last_modified_time

				if not page.site_generator_data["publish_date"]:
					contentTree.warning("There's no '%s' key in the front matter for"
						" '%s' and neither is there a 'source_path' that we can read"
						" the last modified time from, so the date is going to be 0"
						% (FrontMatterConfig.key_publish_date, page.path))

	def aggregate_posts(self):
		## Aggregate folders with no index pages
		# Check if any folder is missing an index page, which would mean
		# we need to create one. NOTE: most of the time I would imagine this
		# would be the case, as the way I understand using folders is to
		# separate different types of content - blog, archive, portfolio, etc.
		folders_with_no_index = list(filter(
			lambda x: isinstance(x, contentTree.Folder) and x.index_page is None,
			self.contentTree.flat(include_index_pages=False)))

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
			folder.index_page = contentTree.AggregatedPage(
				folder.name, sorted(folder.children, reverse=True,
					key=lambda x: x.site_generator_data["publish_date"]))
			self.callbacks.post_contentTree_entity_create(self, folder.index_page)
			if self.num_posts_per_page > 0:
				folder.index_page.paginate(self.num_posts_per_page,
					partial(self.callbacks.post_contentTree_entity_create, self))

		## Aggregate all posts to optionally be used on the home page
		to_globally_aggregate = list(filter(
			lambda x: not self.is_page_func(x),
			self.contentTree.leaves(include_index_pages=False)))

		if self.globally_aggregate_blacklist:
			to_globally_aggregate = [x for x in to_globally_aggregate\
				if x.parent.name not in self.globally_aggregate_blacklist and\
				   str(x.parent.path) not in self.globally_aggregate_blacklist]

		if self.globally_aggregate_whitelist:
			to_globally_aggregate = [x for x in to_globally_aggregate\
				if x.parent.name in self.globally_aggregate_whitelist or\
				   str(x.parent.path) in self.globally_aggregate_whitelist]

		# Check if we have a home index page in which case we'll just store
		# the globally aggregated content and if not we'll create an AggregatedPage
		self.globally_aggregated_posts = to_globally_aggregate
		if not self.contentTree.index_page:
			self.contentTree.index_page = contentTree.AggregatedPage(
				"home", sorted(to_globally_aggregate, reverse=True,
					key=lambda x: x.site_generator_data["publish_date"]))
			self.callbacks.post_contentTree_entity_create(
					self, self.contentTree.index_page)
			if self.num_posts_per_page > 0:
				self.contentTree.index_page.paginate(self.num_posts_per_page,
					partial(self.callbacks.post_contentTree_entity_create, self))

	def build_category_pages(self, parent=None,
			category_accessor=lambda x: x.front_matter.get("category"),
			allow_uncategorized=True, uncategorized_name="Uncategorized",
			leaves_filter=lambda x: True):
		grouped = {}
		for p in filter(lambda x: leaves_filter(x)\
							  and isinstance(x, contentTree.PageOrPost)\
							  and not self.is_page_func(x),
				self.contentTree.leaves()):
			grouped.setdefault(category_accessor(p), []).append(p)

		if None in grouped:
			if not allow_uncategorized:
				raise UncategorizedNotAllowedError("The following pages don't have"
					" categories, but 'allow_uncategorized' is False " + str(grouped[None]))
			else:
				grouped[uncategorized_name] = grouped.pop(None)

		parent = parent or self.contentTree
		self.category_pages = []
		for category, pages in grouped.items():
			aggregatedPage = contentTree.AggregatedPage(category, pages)
			self.callbacks.post_contentTree_entity_create(self, aggregatedPage)
			parent.add_child(aggregatedPage)

			if self.num_posts_per_page > 0:
				self.category_pages += aggregatedPage.paginate(self.num_posts_per_page,
					partial(self.callbacks.post_contentTree_entity_create, self))
			else:
				self.category_pages.append(aggregatedPage)

	def build_archive(self, by_month_format="%B, %Y", by_year_format="%Y"):
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

	def build_archive_pages(self, parent=None, by_month=True, by_year=False):
		if not hasattr(self, "archive"):
			raise ArchivePagesError(
				"The archive must first be initialized using 'build_archive'"
				" before pages can be made out of it.")

		parent = parent or self.contentTree
		archives = (
			(list(self.archive.posts_by_month.items()) if by_month else []),
			(list(self.archive.posts_by_year.items()) if by_year else []))

		if not (archives[0] or archives[1]):
			raise ArchivePagesError("No posts to put in archive")

		archive_pages = []
		for archive in archives:
			archive_pages.append([])
			for archive_key, posts in archive:
				aggregatedPage = contentTree.AggregatedPage(archive_key, posts)
				self.callbacks.post_contentTree_entity_create(self, aggregatedPage)
				parent.add_child(aggregatedPage)

				if self.num_posts_per_page > 0:
					archive_pages[-1] +=\
						aggregatedPage.paginate(self.num_posts_per_page,
							partial(self.callbacks.post_contentTree_entity_create, self))
				else:
					archive_pages[-1].append(aggregatedPage)

		self.archive.pages_by_month = archive_pages[0]
		self.archive.pages_by_year = archive_pages[1]

	def posts(self):
		return [x for x in self.contentTree.leaves() if\
				isinstance(x, contentTree.PageOrPost) and not self.is_page_func(x)]

	def build_navigation(self, filter_func=None,
			group_categories=True, group_archive=True, extra_filter_func=None,
			categories_name="Categories", archive_name="Archive"):
		if hasattr(self, "navigation"):
			contentTree.warning("Navigation already exists, overwriting..")

		extra_filter_func = extra_filter_func or (lambda _: True)
		filter_func = filter_func or (lambda x:\
			(self.is_page_func(x) or x.parent == self.contentTree) and\
			(True if not hasattr(x, "is_index_page") else not x.is_index_page()) and\
			(True if not isinstance(x, contentTree.PaginatedAggregatedPage) else\
			 x.pagination.page_number == 1))

		navigatable_tree = self.contentTree.filter(
			lambda x: filter_func(x) and extra_filter_func(x), True)

		if group_categories and getattr(self, "category_pages", None):
			category_paths = [p.path for p in self.category_pages]
			navigatable_tree.group(categories_name,
				[p for p in navigatable_tree.flat() if p.path in category_paths])

		if group_archive and getattr(self, "archive", None):
			archive_paths = [p.path for p in\
				self.archive.pages_by_month + self.archive.pages_by_year]
			navigatable_tree.group(archive_name,
				[p for p in navigatable_tree.flat() if p.path in archive_paths])

		self.navigation = navigatable_tree.as_dict(lambda x: x.href)

	def render(self, to_renderable_page=RenderablePage, to_site_info=SiteInfo,
			markup_processor_func=markdown.markdown if markdown else None,
			**kwargs):
		if self.build_directory.exists():
			shutil.rmtree(self.build_directory)

		self.build_directory.mkdir()

		# We want to render aggregated pages last, so we make sure that all
		# posts that they aggregate already have their content processed
		for leaf in sorted(self.contentTree.leaves(),
				key=lambda x: len(getattr(x, "aggregated_posts", []))):
			# Make sure the content has been read and processed
			leaf.parse_front_matter_and_content()
			leaf.process_content(markup_processor_func)

			path = leaf.render_path(self.build_directory)

			if not path.parent.exists():
				os.makedirs(path.parent)

			with open(path, "w") as f:
				f.write(self.renderer.render("default.html",
					page=to_renderable_page(leaf),
					site_info=to_site_info(self), **kwargs))


class Jinja2Renderer:
	def __init__(self, template_directories):
		self.environment = jinja2.Environment(
			loader=jinja2.ChoiceLoader(
				[jinja2.FileSystemLoader(x) for x in template_directories]),
			autoescape=jinja2.select_autoescape())

	def render(self, template, **render_data):
		return self.environment.get_template(template).render(**render_data)


class Archive:
	def __init__(self, posts_by_month, posts_by_year):
		self.posts_by_month = posts_by_month
		self.posts_by_year = posts_by_year
		self.pages_by_month = []
		self.pages_by_year = []

	def as_navigation_dict(self):
		return {
			"by_month": [(p.name, p.href) for p in self.pages_by_month\
				if p.pagination.page_number == 1],
			"by_year": [(p.name, p.href) for p in self.pages_by_year\
				if p.pagination.page_number == 1]
			}
