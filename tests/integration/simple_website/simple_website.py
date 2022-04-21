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
	site = pygeon.Site(name="Simple Website", directory=Path(__file__).parent)
	site.build_content_tree()

	site.content.get(".").add_child(pygeon.AggregatedPage("sup", site.content.get("blog").children))

	site.content.titlify()

	print(site.content)

	site.render()
