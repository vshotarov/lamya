from pathlib import Path
import markdown
import shutil
import jinja2


def build(site_name, root_dir=None):
	root_dir = Path(root_dir or os.getcwd())

	# Read config file
	config_file = root_dir / (site_name + ".py")

	config = {}
	with open(config_file) as f:
		exec(f.read(), {}, config)
	
	# Create Site object from config
	site = Site(site_name, config=config)
	
	# Build
	build_dir = root_dir / "build" # NOTE: I'm not keen on the name build

	if build_dir.exists():
		shutil.rmtree(build_dir)
	
	build_dir.mkdir()

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

			html = markdown.markdown(source_content)
			# TODO: Process html

			relative_path = path.relative_to(root_dir / "content")

			pages.append(Page(name=relative_path.stem,
				description="desc", href=to_href(relative_path), content=html,
				file_path=Path("index.html") if relative_path == Path("index.md")\
						  else relative_path.with_suffix("") / "index.html",
				front_matter=evaluated_front_matter))

			if relative_path.parent == Path("."):
				site.navigation_pages.append(pages[-1])
			else:
				# This is further down the hierarchy, so let's store all the
				# unique parents to content, so we can create folders for them
				hierarchy_levels.add(relative_path.parent)

		if path.suffix.lower() == ".html":
			raise NotImplementedError("No support for compiling .html files yet")

	# Insert home page if it's not manually defined
	if not any([p.file_path == Path("index.html") for p in pages]):
		pages.append(Page(name="home",description="home desc",
			href="/",content="",file_path=Path("index.html")))
		site.navigation_pages.insert(0,pages[-1])
	else:
		# Make sure the home page is at the front
		home_page = next(filter(lambda p: p.file_path == Path("index.html"), pages))
		site.navigation_pages.remove(home_page)
		site.navigation_pages.insert(0, home_page)
		home_page.name = "home" # NOTE: Expose this to the front matter
	
	# Render
	environment = jinja2.Environment(
		loader=jinja2.FileSystemLoader(
			searchpath=Path(__file__).parent / "resources" / "templates"),
		trim_blocks=True, autoescape=True)

	# Go through all hierarchy levels and create the folders
	for hl in hierarchy_levels:
		hl_in_build = build_dir / hl
		if not hl_in_build.exists():
			hl_in_build.mkdir(exist_ok=True)

		# If there's no defined index page for that level and it's included
		# in the config `aggregate` section, we need to create an index page
		# aggregating all of the content at that level
		relative_hl = root_dir / "content" / hl
		level_index_page = next(
			filter(lambda p: p.file_path == Path(hl / "index.html"), pages), None)
		if not level_index_page:
			if hl.__str__() in site.aggregate:
				pages_at_this_level = filter(lambda p: p.file_path.parent.parent == hl, pages)

				# TODO: Aggregate properly with titles, potentially using pages, excerpts, etc.
				aggregated_content = "\n".join([
					("<a href=%s>%s</a>\n" % (p.href, p.front_matter.get("title",p.name)))\
					+ p.content for p in pages_at_this_level])

				level_index_page = Page(name=hl.stem, description=hl.stem + " desc",
					href=to_href(hl),content=aggregated_content,file_path=hl / "index.html")
				pages.append(level_index_page)
			else:
				# Otherwise, seems like we really don't want an index page at
				# this level, so let's use the 404 template to prevent the web browser
				# to create open a file browser
				with open(hl_in_build / "index.html", "w") as f:
					# NOTE: Creating a dummy page here doesn't feel great. I need
					# a way of separating the 404 from the rest
					pages.append(Page(name="404",description="",href="",
						content="",file_path=hl / "index.html",template="404.html"))

		# If it's a top level directory add it to the navigation
		if not hl.parent.stem:
			site.navigation_pages.append(level_index_page)

	for p in pages:
		page_path = build_dir / p.file_path
		page_path.parent.mkdir(exist_ok=True)
		with open(page_path, "w") as f:
			f.write(environment.get_template(p.template).render(site=site,page=p))

class Page(object):
	def __init__(self, name, description, href, content, file_path,
			template="index.html", front_matter={}):
		self.name = name
		self.description = description
		self.href = href
		self.content = content
		self.file_path = file_path
		self.template = template
		self.front_matter = front_matter 

class Site(object):
	def __init__(self, name, config):
		# Initialize defaults
		self.name = name
		self.title_template = "{site.name} - {page.name}"
		self.aggregate = []

		# Read config
		for k,v in config.items():
			setattr(self, k, v)

		self.navigation_pages = []

def to_href(path: Path) -> str:
	if path == Path("index.md"):
		return "/"
	else:
		return "/" + path.with_suffix("").__str__()
