import pygeon
import jinja2
import markdown
import shutil
import os
from pathlib import Path


url = "https://simple_website.xyz"
title_template = "{page.name} - {page.description}"
navigation = [
		{"name": "homeee", "href": "/"},
		{"name": "aboouuut", "href": "/about", "children": [
			{"name": "child1", "href": "/"},
			{"name": "child2", "href": "/about/child2"},
			{"name": "contact", "href": "/contact"}
		]},
		{"name": "contact", "href": "/contact"}
]

def build():
	## Preprocess stage
	# Read the content structure and build a ContentTree out of it
	site_path = Path(__file__).parent
	content = pygeon.ContentTree.from_directory(site_path / "content")

	## Process stage
	# Aggregate all blog posts in the blog index page
	content.get("blog").add_child(pygeon.AggregatedPage(
		"index", list(content.get("blog").children), is_index=True))

	# Let's give each page a nice 'title'
	content.map_in_place(
		lambda x: setattr(x, "title",
			(x.parent.name if x.is_index else x.name).replace("_"," ").title()))

	# All first level content i.e. content leaves whose parent is the root will
	# be treated as pages rather than posts, so let's split our leaves into
	# `pages` and `posts` groups
	page_post_groups = {
		k: list(filter(lambda x: isinstance(x, pygeon.Post), v)) for k,v in\
		content.group_by(lambda x: "page" if x.parent == content else "post").items() }

	# Let's use the pages as our navigation
	# It would be good to also add any aggregated hierarchies to the navigation,
	# such as the 'blog' aggregated page from above, since technically the
	# 'blog' page also is a first level page, albeit it's also a hierarchy
	top_level_aggregated_pages = content.filter(
		lambda x: isinstance(x, pygeon.AggregatedPage)
			  and x.parent and x.parent.parent == content)
	navigation_pages = page_post_groups["page"] + top_level_aggregated_pages
	navigation_pages.remove(content.get("index")) # no home page in the navigation
	navigation = [(p.title, str(p.href())) for p in navigation_pages]

	## Render stage
	build_directory = site_path / "build"
	if build_directory.exists():
		shutil.rmtree(build_directory)

	build_directory.mkdir()

	# Build the renderer
	renderer = jinja2.Environment(loader=jinja2.FileSystemLoader(site_path / "templates"),
		autoescape=jinja2.select_autoescape())

	# Define a function for writing a ContentTree class into a processed html file
	def write(page):
		if isinstance(page, pygeon.Leaf):
			page_path = build_directory / page.href().relative_to("/") / "index.html"
			source = page.get_source() if page.source_path else ""
			template = "default.html"
		elif not page.has_index:
			page_path = build_directory / page.path() / "index.html"
			source = ""
			template = "404.html"
		else:
			return

		if not page_path.parent.exists():
			os.makedirs(page_path.parent)

		with open(page_path, "w") as f:
			f.write(renderer.get_template("default.html").render(
				content=markdown.markdown(source)))

	# Perform the writing to disk
	content.map_in_place(write)
