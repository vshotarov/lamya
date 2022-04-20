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
	content.titlify()
	print(content)
	print(content.get("Blog/{0}"))
	content.get(".").add_child(content.get("Blog/{1}"))
	print(content)
