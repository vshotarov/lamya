import pygeon
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
	content = pygeon.ContentTree.from_directory(Path(__file__).parent / "content")

	## Process stage
	# Aggregate all blog posts in the blog page
	content.get("blog").add_child(pygeon.AggregatedPage("index", content.get("blog").children))

	## Render stage


	print(content)
