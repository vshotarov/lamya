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
	content = pygeon.ContentTree.from_directory(Path(__file__).parent / "content")

	content.get(".").add_child(pygeon.AggregatedPage("sup", content.get("blog").children))

	content.titlify()

	print(content)
