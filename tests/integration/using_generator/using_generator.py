import pygeon.site_generator
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
	site = pygeon.site_generator.SiteGenerator(name="Test Using Generator",
		content_directory=site_path / "content",
		theme_directory=site_path / "theme",
		templates_directory=site_path / "templates",
		static_directory=site_path / "static",
		build_directory=site_path / "build")
	site.process_content_tree()
	print(site.contentTree.group(
		lambda x: x.user_data["front_matter"].get("category")\
			if x.user_data else None))
	print(site.contentTree.get("blog/{1}").user_data["publish_date"], "<<")

	print(site.contentTree)
