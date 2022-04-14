from pathlib import Path
import markdown
import shutil
import jinja2
from datetime import datetime
import time
import re
import math
import html
import xml.etree.cElementTree as ET
from xml.dom import minidom
from copy import deepcopy


class PygeonError(Exception):
	pass


def build(site_name, root_dir=None):
	root_dir = Path(root_dir or os.getcwd())

	# Read config file
	config_file = root_dir / (site_name + ".py")

	config = {}
	with open(config_file) as f:
		exec(f.read(), {}, config)

	# Gather the theme information
	# NOTE: We'd likely want the theme to be specified by the config, rather
	# than directly reading it from the theme folder
	theme_path = Path(config.get("theme_path", root_dir / "theme"))
	
	# Create Site object from config
	site = Site(site_name, config=config)
	
	# Build
	build_dir = root_dir / "build" # NOTE: I'm not keen on the name build

	if build_dir.exists():
		shutil.rmtree(build_dir)
	
	build_dir.mkdir()

	# Copy over static content
	# First copy from the theme, so it can then be overwritten by any custom
	# static content
	copy_static_data(theme_path / "static", build_dir)
	# Then from the site
	copy_static_data(root_dir / "static", build_dir)

	# Go through each defined content entry
	pages = []
	hierarchy_levels = set([])
	for path in (root_dir / "content").glob("**/*"):
		if not path.is_file():
			continue

		if path.suffix.lower() == ".md":
			with open(path) as f:
				source = f.read()

			# TODO: Process source
			front_matter = ""
			source_content = ""
			write_to_front_matter = False
			for line in source.splitlines():
				if line.lstrip().rstrip() == "+++":
					write_to_front_matter = not write_to_front_matter
					continue
				if write_to_front_matter:
					front_matter += line + "\n"
				else:
					source_content += line + "\n"

			evaluated_front_matter = {}
			exec(front_matter, {}, evaluated_front_matter)

			# Process date if it exists in the front matter
			if "publish_date" in evaluated_front_matter.keys():
				evaluated_front_matter["publish_date"] = datetime.strptime(
					evaluated_front_matter["publish_date"], "%d-%m-%Y")
			evaluated_front_matter["auto_publish_date"] =\
				datetime.fromtimestamp(path.stat().st_mtime)

			# Process shortcodes
			shortcode_processed_content = source_content
			for shortcode in re.finditer("\[%-\s*(\S*)\s*(.*)-%\]", source_content):
				shortcode_processed_content = shortcode_processed_content.replace(
					shortcode.group(0), process_shortcode(shortcode.group(1),
						shortcode.group(2) if len(shortcode.groups()) else ""))

			content_html = markdown.markdown(shortcode_processed_content,
				extensions=["tables","fenced_code"])
			# TODO: Process html

			relative_path = path.relative_to(root_dir / "content")

			# Build a smarter excerpt
			if "excerpt" not in evaluated_front_matter.keys():
				# Find the first space after the 150th character
				plain_content = remove_html(content_html)
				for char_pos, char in enumerate(plain_content[150:]):
					if char == " ":
						break
				if len(plain_content) < 150:
					excerpt = plain_content
				else:
					excerpt = plain_content[:150+char_pos] + "..."
			else:
				excerpt = evaluated_front_matter["excerpt"]

			pages.append(Page(name=evaluated_front_matter.get("title", relative_path.stem),
				description="desc", href=to_href(relative_path), content=content_html, excerpt=excerpt,
				file_path=relative_path.with_suffix(".html") if relative_path.name == "index.md"\
						  else relative_path.with_suffix("") / "index.html",
				front_matter=evaluated_front_matter))

			if relative_path.parent == Path("."):
				site.navigation.append(pages[-1])
			else:
				# This is further down the hierarchy, so let's store all the
				# unique parents to content, so we can create folders for them
				hierarchy_levels.add(relative_path.parent)

		if path.suffix.lower() == ".html":
			raise NotImplementedError("No support for compiling .html files yet")

	# All of the pages defined up to now are read directly from the content
	# folder, so let's store them separately before we move on to procedurally
	# generate some pages as well
	content_pages = deepcopy(pages)
	
	# Render
	environment = jinja2.Environment(
		loader=jinja2.ChoiceLoader([
			jinja2.FileSystemLoader(
				searchpath=theme_path / "templates"),
			jinja2.FileSystemLoader(
				searchpath=Path(__file__).parent / "resources" / "templates")
		]),
		trim_blocks=True, autoescape=True)

	# Go through all hierarchy levels and create the folders
	for hl in sorted(hierarchy_levels, key=lambda x:x.__str__().count("/")):
		hl_in_build = build_dir / hl
		if not hl_in_build.exists():
			hl_in_build.mkdir(exist_ok=True)

		# If there's no defined index page for that level and it's included
		# in the config `aggregate` section, we need to create an index page
		# aggregating all of the content at that level
		level_index_page = next(
			filter(lambda p: p.file_path == Path(hl / "index.html"), pages), None)
		if not level_index_page:
			hierarchy_entry_point = None
			if hl.__str__() in site.aggregate:
				posts_at_this_level = list(
					filter(lambda p: p.file_path.parent.parent == hl, pages))
				site.all_aggregated_posts += posts_at_this_level

				paginated_pages = paginate(posts_at_this_level,
					config.get("pagination",float("inf")), hl, hl, hl.stem.__str__())

				if paginated_pages:
					pages += paginated_pages
					hierarchy_entry_point = paginated_pages[0]

					with open(hl_in_build / "index.html", "w") as f:
						# NOTE: Creating a dummy page here doesn't feel great. I need
						# a way of separating the 404 from the rest
						# NOTE: Also, duplicate code
						pages.append(Page(name="404",description="",href="",
							content="",file_path=hl / "index.html",template="404.html"))
				else:
					level_index_page = Page(name=hl.stem, description=hl.stem + " desc",
						href=to_href(hl),content="",file_path=hl / "index.html",
						aggregated_pages=posts_at_this_level)
					pages.append(level_index_page)
					hierarchy_entry_point = level_index_page
			else:
				# Otherwise, seems like we really don't want an index page at
				# this level, so let's use the 404 template to prevent the web browser
				# to create open a file browser
				with open(hl_in_build / "index.html", "w") as f:
					# NOTE: Creating a dummy page here doesn't feel great. I need
					# a way of separating the 404 from the rest
					pages.append(Page(name="404",description="",href="",
						content="",file_path=hl / "index.html",template="404.html"))
		else:
			level_index_page.name = hl
			hierarchy_entry_point = level_index_page

		# If it's a top level directory add it to the navigation
		if not hl.parent.stem and hierarchy_entry_point:
			site.navigation.append(hierarchy_entry_point)

	# Generate an archive page
	if getattr(site, "create_archive", False):
		archive_page = Page("archive", description="", href="/archive",
			content="", file_path=Path("archive") / "index.html")

		for p in pages:
			date = p.front_matter.get("publish_date", p.front_matter.get("auto_publish_date"))

			if p.is_top_level or not date:
				continue

			if date.year not in site.archive["by_year"].keys():
				site.archive["by_year"][date.year] = []
			site.archive["by_year"][date.year].append(p)

			if date.strftime("%B, %Y") not in site.archive["by_month"].keys():
				site.archive["by_month"][date.strftime("%B, %Y")] = []
			site.archive["by_month"][date.strftime("%B, %Y")].append(p)

		pages.append(archive_page)

		# Create pages for each month of the archive
		for month, posts in site.archive["by_month"].items():
			pages.append(Page(month, description="",
				href=to_href(Path("archive") / month.replace(", ","_")),
				content="", file_path=Path("archive") / month.replace(", ","_") / "index.html",
				aggregated_pages=posts))

		# Check if there already is an archive page in the navigation and if so
		# don't add it again
		if not any([p.href == "/archive" for p in site.navigation]):
			site.navigation.append(archive_page)
	
	# If we are paginating and all_aggregated_posts has more than one page of
	# content in it, we have to paginate it as well
	site.all_aggregated_posts_paginated = paginate(
		site.all_aggregated_posts, config.get("pagination", float("inf")),
		Path(""), Path(""), "home")
	if site.all_aggregated_posts_paginated:
		site.all_aggregated_posts_paginated[0].href = "/"
		site.all_aggregated_posts_paginated[0].file_path = "index.html"
		site.all_aggregated_posts_paginated[1].pagination_nav["prev"] = "/"

	# Insert home page if it's not manually defined
	if not any([p.file_path == Path("index.html") for p in pages]):
		if not config.get("aggregate_all_on_home_page", False):
			pages.append(Page(name="home",description="home desc",
				href="/",content="",file_path=Path("index.html")))
			site.navigation.insert(0,pages[-1])
		else:
			if site.all_aggregated_posts_paginated:
				pages += site.all_aggregated_posts_paginated
				site.navigation.insert(0,site.all_aggregated_posts_paginated[0])
			else:
				pages.append(Page(name="home",description="home desc",
					href="/",content="",file_path=Path("index.html"),
					aggregated_pages=site.all_aggregated_posts))
				site.navigation.insert(0,pages[-1])
	else:
		# Make sure the home page is at the front
		home_page = next(filter(lambda p: p.file_path == Path("index.html"), pages))
		site.navigation.remove(home_page)
		site.navigation.insert(0, home_page)
		home_page.name = "home" # NOTE: Expose this to the front matter
	
	# If we have defined navigation in the config use that, otherwise
	# conform the format of the aggregated navigation to the config's one
	site.navigation = config.get("navigation",
		[{"href":p.href, "name":p.name, "children":[]} for p in site.navigation])

	# Write the html to files
	for p in pages:
		page_path = build_dir / p.file_path
		page_path.parent.mkdir(exist_ok=True)
		with open(page_path, "w") as f:
			f.write(environment.get_template(p.template).render(site=site,page=p))

	# Write the RSS feed
	utc_offset = time.localtime().tm_gmtoff / 60 / 60
	rss_date_format = "%a, %d %b %Y %H:%M:%S " +\
		("%s%02d00" % ("+" if utc_offset >= 0 else "", utc_offset))
	rss_tag = ET.Element("rss", attrib={"version":"2.0",
		"xmlns:atom":"http://www.w3.org/2005/Atom"})
	channel_tag = ET.SubElement(rss_tag, "channel")
	for k,v in {"title": site.name, "link": site.url, "description": site.description,
			"pubDate": datetime.now().strftime(rss_date_format),
			"docs":"https://validator.w3.org/feed/docs/rss2.html#comments"}.items():
		ET.SubElement(channel_tag, k).text = v
	ET.SubElement(channel_tag, "atom:link", attrib={"href":site.url + "/rss", "rel":"self",
		"type":"application/rss+xml"})

	for cp in sorted(content_pages,
			key=lambda x:x.front_matter.get("publish_date", x.front_matter["auto_publish_date"])):
		item_tag = ET.SubElement(channel_tag, "item")
		for k,v in {"title": cp.name, "link": site.url + "/" + cp.href.__str__(),
				"description": "<![CDATA[%s]]>" % cp.content,
				"pubDate": cp.front_matter.get("publish_date", cp.front_matter["auto_publish_date"]
					).strftime(rss_date_format)}.items():
			ET.SubElement(item_tag, k).text = v
		ET.SubElement(item_tag, "guid", attrib={"isPermaLink":"true"}).text = site.url + "/" + cp.href.__str__()
		ET.SubElement(item_tag, "source", attrib={"url": site.url + "/rss"}).text = site.name

	with open(build_dir / "rss", "w") as f:
		f.write(html.unescape(minidom.parseString(ET.tostring(rss_tag,method="xml")).toprettyxml()))


class Page(object):
	def __init__(self, name, description, href, content, file_path, excerpt="",
			template="index.html", aggregated_pages=[], front_matter={},
			pagination_nav={"prev":None,"next":None}):
		self.name = name
		self.description = description
		self.href = href
		self.content = content
		self.file_path = file_path
		self.excerpt = excerpt
		self.template = template
		self.aggregated_pages = aggregated_pages
		self.front_matter = front_matter 
		self.is_top_level = len([x for x in href.split("/") if x]) <= 1
		self.pagination_nav = pagination_nav

class Site(object):
	def __init__(self, name, config):
		# Initialize defaults
		self.name = name
		self.title_template = "{site.name} - {page.name}"
		self.description = ""
		self.aggregate = []
		self.all_aggregated_posts = []
		self.all_aggregated_posts_paginated = []
		self.archive = {"by_month":{}, "by_year":{}}
		self.build_datetime = datetime.now()

		# Read config
		for k,v in config.items():
			setattr(self, k, v)

		self.navigation = []

def to_href(path: Path) -> str:
	if path.name == "index.md":
		return "/" + path.parent.__str__()
	else:
		return "/" + path.with_suffix("").__str__()

def copy_static_data(from_static_dir: Path, build_dir: Path):
	if from_static_dir.exists():
		for path in from_static_dir.glob("**/*"):
			if not path.is_file():
				continue

			build_path = build_dir / path.relative_to(from_static_dir)
			if not build_path.parent.exists():
				build_path.parent.mkdir(parents=True)

			shutil.copy2(path.resolve(), build_path)

def process_shortcode(_type, args_string):
	args = args_string.strip().split(" ") # NOTE: very naive

	if _type == "gist":
		if len(args) != 2:
			raise PygeonError("gist shortcode requires exactly 2 arguments. It got " + str(args))
		return '<script type="application/javascript" src="https://gist.github.com/%s/%s.js"></script>' % (args[0], args[1])
	if _type == "vimeo":
		if len(args) != 1:
			raise PygeonError("vimeo shortcode requires exactly 1 arguments. It got " + str(args))
		return """<div style="position: relative; padding-bottom: 56.25%%; height: 0; overflow: hidden;">
  <iframe src="https://player.vimeo.com/video/%s" style="position: absolute; top: 0; left: 0; width: 100%%; height: 100%%; border:0;" title="vimeo video" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>
</div>""" % args[0]
	
	return "HELLO"

def remove_html(x):
	# https://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string
	CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
	return re.sub(CLEANR, "", x)

def paginate(posts, pagination, href_base, file_path_base, name):
	num_pages = math.ceil(len(posts) / pagination)
	pages = []
	if num_pages > 1:
		per_page = int(pagination)
		for page in range(num_pages):
			paginated_posts = posts[(page*per_page):((page+1)*per_page)]
			level_index_page = Page(name=name, description=name + " desc",
				href=to_href(href_base / ("page%i" % (page+1))),content="",
				file_path=file_path_base / ("page%i" % (page+1)) / "index.html",
				aggregated_pages=paginated_posts,
				pagination_nav={
					"prev":to_href(href_base / ("page%i" % (page))) if page != 0 else None,
					"next":to_href(href_base / ("page%i" % (page+2))) if page != num_pages-1 else None})
			pages.append(level_index_page)
	return pages
