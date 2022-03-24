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
	site = Site.from_config(config)
	
	# Build
	build_dir = root_dir / "build" # NOTE: I'm not keen on the name build

	if build_dir.exists():
		shutil.rmtree(build_dir)
	
	build_dir.mkdir()

	# Go through each defined content entry
	pages = []
	for path in (root_dir / "content").glob("**/*"):
		if not path.is_file():
			continue

		if path.suffix.lower() == ".md":
			with open(path) as f:
				source = f.read()

			# TODO: Process source
			html = markdown.markdown(source)
			# TODO: Process html

			relative_path = path.relative_to(root_dir / "content")

			pages.append(Page(name=relative_path.stem,
				description="desc", href=to_href(relative_path),
				content=html, file_path=relative_path.with_suffix(".html")))

			if relative_path.parent == Path("."):
				site.navigation_pages.append(pages[-1])

		if path.suffix.lower() == ".html":
			raise NotImplementedError("No support for compiling .html files yet")

	# Insert home page if it's not manually defined
	if not any([p.file_path == Path("index.html") for p in pages]):
		pages.append(Page(name="home",description="home desc",href="/",content="",
			file_path=Path("index.html")))
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

	for p in pages:
		with open(build_dir / p.file_path, "w") as f:
			f.write(environment.get_template("index.html").render(site=site,page=p))

class Page(object):
	def __init__(self, name, description, href, content, file_path):
		self.name = name
		self.description = description
		self.href = href
		self.content = content
		self.file_path = file_path

class Site(object):
	def __init__(self, title_template):
		self.title_template = title_template
		self.navigation_pages = []
	
	@staticmethod
	def from_config(config):
		return Site(title_template=jinja2.Template(config["TITLE_TEMPLATE"]))

def to_href(path: Path) -> str:
	if path == Path("."):
		return "/"
	else:
		return "/" + path.with_suffix(".html").__str__()
