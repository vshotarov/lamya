from . import contentTree
from . import contentProcessing
from pathlib import Path
from datetime import datetime
from functools import partial
import os
try:
	from markdown import markdown
except ImportError:
	markdown = None
try:
	import jinja2
except ImportError:
	jinja2 = None


class AggregateError(Exception):
	pass

class UncategorizedNotAllowedError(Exception):
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
		pass


class SiteGenerator:
	def __init__(self, name, content_directory="content", theme_directory="theme",
			static_directory="static", templates_directory="templates",
			build_directory="build", locally_aggregate_whitelist=[],
			locally_aggregate_blacklist=[], globally_aggregate_whitelist=[],
			globally_aggregate_blacklist=[], num_posts_per_page=5,
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

	def initialize_renderer(self):
		if jinja2 is None:
			raise NotImplementedError("jinja2 was not found, so it either"
				" needs to be installed or you need to overwrite the"
				" 'initialize_renderer' method on the 'Site' class to use"
				" your own templating engine.")

		self.renderer = Jinja2Renderer([
			self.templates_directory, self.theme_directory / "templates"])

	def process_content_tree(self):
		## At this point we have the main hierarchy. Let's now read the source
		# store their front matter in the .user_data field for each page, so
		# we can start optionally grouping the content using different heuristics
		for page in self.contentTree.leaves():
			# Store the front matter
			source = page.source
			if source:
				# Let's cache the source, so we don't read it from disk, if it's
				# ever requested again
				page._source = source
				page.user_data["front_matter"], page.user_data["raw_content"] =\
					contentProcessing.split_front_matter(
						source, self.front_matter_delimiter)
			else:
				page.user_data["front_matter"] = {}

			# We will be sorting content by date, so let's make sure all content
			# has some sort of a date, either explicit in the front matter or
			# we take the last modified time as a backup
			if "publish_date" not in page.user_data:
				# Use an `if`, so we can support the user manually setting
				# the publish date beforehand if need by
				last_modified_time = datetime.fromtimestamp(
					os.path.getmtime(page.source_path) if page.source_path else 0)

				front_matter_publish_date = page.user_data["front_matter"].get(
					FrontMatterConfig.key_publish_date)
				front_matter_publish_date = datetime.strptime(
					front_matter_publish_date, FrontMatterConfig.date_format) if\
					front_matter_publish_date else None

				page.user_data["publish_date"] =\
					front_matter_publish_date or last_modified_time

				if not page.user_data["publish_date"]:
					contentTree.warning("There's no '%s' key in the front matter for"
						" '%s' and neither is there a 'source_path' that we can read"
						" the last modified time from, so the date is going to be 0"
						% (FrontMatterConfig.key_publish_date, self.path))

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
					key=lambda x: x.user_data["publish_date"]),
					user_data={"front_matter":{}})
			self.callbacks.post_contentTree_entity_create(self, folder.index_page)
			if self.num_posts_per_page > 0:
				folder.index_page.paginate(self.num_posts_per_page)

		## Aggregate all posts to optionally be used on the home page
		to_globally_aggregate = list(filter(
			lambda x: not self.is_page_func(x),
			self.contentTree.leaves(include_index_pages=False)))

		if self.globally_aggregate_blacklist:
			to_globally_aggregate = [x for x in to_globally_aggregate\
				if x.name not in self.globally_aggregate_blacklist and\
				   str(x.path) not in self.globally_aggregate_blacklist]

		if self.globally_aggregate_whitelist:
			to_globally_aggregate = [x for x in to_globally_aggregate\
				if x.name in self.globally_aggregate_whitelist or\
				   str(x.path) in self.globally_aggregate_whitelist]

		# Check if we have a home index page in which case we'll just store
		# the globally aggregated content and if not we'll create an AggregatedPage
		self.globally_aggregated_posts = to_globally_aggregate
		if not self.contentTree.index_page:
			self.contentTree.index_page = contentTree.AggregatedPage(
				"home", to_globally_aggregate, user_data={"front_matter": {}})
			self.callbacks.post_contentTree_entity_create(
					self, self.contentTree.index_page)
			if self.num_posts_per_page > 0:
				self.contentTree.index_page.paginate(self.num_posts_per_page)

	def build_category_pages(self, parent=None,
			category_accessor=lambda x: x.user_data.get("front_matter",{}).get("category"),
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
		for category, pages in grouped.items():
			aggregatedPage = contentTree.AggregatedPage(
				category, pages, {"front_matter":{}})
			parent.add_child(aggregatedPage)

			if self.num_posts_per_page > 0:
				aggregatedPage.paginate(self.num_posts_per_page)

class Jinja2Renderer:
	def __init__(self, template_directories):
		self.environment = jinja2.Environment(
			loader=jinja2.ChoiceLoader(
				[jinja2.FileSystemLoader(x) for x in template_directories]),
			autoescape=jinja2.select_autoescape())

	def render(self, template, **render_data):
		return self.environment.get_template(template).render(**render_data)
