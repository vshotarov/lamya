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
	content.get("blog").index_page = pygeon.AggregatedPage(
		"blog", content.get("blog").children, source="")

	# All first level content i.e. content leaves whose parent is the root will
	# be treated as pages rather than posts, so let's split our leaves into
	# `pages` and `posts` groups
	page_post_groups = content.group(
		lambda x: "page" if x.parent == content else "post", False)

	# Build a navigation structure
	navigation = content.filter(lambda x: x.parent.name != "blog").as_dict(lambda x: x.path.__str__())

	# Render
	build_directory = site_path / "build"
	if build_directory.exists():
		shutil.rmtree(build_directory)

	build_directory.mkdir()

	renderer = jinja2.Environment(
		loader=jinja2.FileSystemLoader(site_path / "templates"),
		autoescape=jinja2.select_autoescape())

	def render_single(pageOrPost):
		path = pageOrPost.render_path(build_directory)

		if not path.parent.exists():
			os.makedirs(path.parent)

		with open(path, "w") as f:
			f.write(renderer.get_template("default.html").render(
				content=markdown.markdown(pageOrPost.source),
				aggregated_posts=getattr(pageOrPost, "aggregated_posts", [])))

	for pageOrPost in content.leaves():
		render_single(pageOrPost)
