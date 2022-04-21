from pathlib import Path
import os
import markdown
from datetime import datetime
from copy import deepcopy
import shutil

# NOTE: Put in a separate module, so it can be optional
import jinja2


class ContentTree(object):
	def __init__(self, name, source_path):
		self.name = name
		self.title = name
		self._parent = None
		self._source_path = source_path

		self._children = []

	@property
	def parent(self):
		return self._parent

	@parent.setter
	def parent(self, new_parent):
		self._parent = new_parent

	@property
	def children(self):
		return self._children

	@children.setter
	def children(self, new_children):
		self._children = new_children

	def add_child(self, child):
		child.parent = self
		self.children.append(child)

	def remove_child(self, child):
		self.children.remove(child)

	@property
	def source_path(self):
		return self._source_path

	@source_path.setter
	def source_path(self, new_source_path):
		self._source_path = new_source_path

	def pprint(self, level=0):
		return "%s%s(%s) {\n%s%s\n%s}" % (" "*level, self.__class__.__name__,
			self.title, " "*(level+1),
			("\n" + " "*(level+1)).join([x.pprint(level+1) for x in self.children]),
			" "*(level+1))

	def __str__(self):
		return self.pprint()

	def __repr__(self):
		return self.__str__()
	# end of basic tree class functions

	# static constructors
	@staticmethod
	def from_directory(directory):
		root = Root("/", Path(directory))

		def recursive_builder(parent):
			for child_path in sorted(parent.source_path.iterdir()):
				child = recursive_builder(ContentTree(child_path.name, child_path))\
					if child_path.is_dir() else Post(child_path.stem, child_path)
				parent.add_child(child)

			return parent

		recursive_builder(root)

		return root
	# end of static constructors

	# tree accessors
	def get(self, path):
		"""Returns the sub tree at that path.

		The path accepts the following format for accessing elements by index
		in their children list - {%i}, e.g. {0} for the first element.

		NOTE: The path MUST NOT start with a '/'.
		"""
		path = Path(path)

		if not path.parts:
			return self

		try:
			children = self.children
		except AttributeError as e:
			raise AttributeError("Can't `get` a path from a leaf node")

		next_step = None
		for i, child in enumerate(children):
			if path.parts[0] in ["{%i}" % i, child.name]:
				next_step = child
				break

		if next_step:
			if str(path.parent) in [".","/"]:
				return next_step
			else:
				return next_step.get("/".join(path.parts[1:]))
		else:
			raise LookupError(
				"The path '%s' does not exist under %s" % (path, self))

	def flat(self):
		def flatten(tree, aggregated=[]):
			aggregated.append(tree)

			try:
				for child in tree.children:
					flatten(child, aggregated)
			except AttributeError:
				pass

			return aggregated

		return flatten(self)

	def leaves(self, recursively=True):
		leaves = []
		try:
			for child in self.children:
				if isinstance(child, Leaf):
					leaves.append(child)
				elif recursively:
					leaves += child.leaves()
		except AttributeError as e:
			raise AttributeError("A Leaf object doesn't contain any `leaves`")

		return leaves

	def path(self):
		if self.parent:
			return self.parent.path() / self.name
		else:
			return Path()

	# end of tree accessors

	# pygeon content operators (until the end of the class definition)
	def map(self, func):
		copy = deepcopy(self)
		func(copy)

		for child in copy.children:
			try:
				child.map_in_place(func)
			except AttributeError:
				pass

		return copy

	def map_in_place(self, func):
		func(self)

		for child in self.children:
			try:
				child.map_in_place(func)
			except AttributeError:
				pass

	def titlify(self, title_func=lambda x:\
			setattr(x, "title", x.name.replace("_"," ").title())):
		self.map_in_place(title_func)


class Root(ContentTree):
	def __init__(self, name, source_path):
		super(Root, self).__init__(name=name, source_path=source_path)


class Leaf(ContentTree):
	def __init__(self, name, source_path):
		super(Leaf, self).__init__(name=name, source_path=source_path)

		self.template = None

	@property
	def children(self):
		raise AttributeError("Leaf nodes can't have children")

	@children.setter
	def children(self, _):
		raise AttributeError("Leaf nodes can't have children")

	def pprint(self, level=0):
		return "%s%s(%s)" % (" "*level, self.__class__.__name__, self.title)

	def source(self):
		source = ""
		if self.source_path:
			with open(self.source_path, "r") as f:
				source = f.read()

		return source

class Post(Leaf):
	def __init__(self, name, source_path, template="default.html"):
		super(Post, self).__init__(name=name, source_path=source_path)

		self.template = template


class AggregatedPage(Leaf):
	def __init__(self, name, aggregated_posts, source_path=None,
			template=["list_of_posts.html", "default.html"]):
		# NOTE: Of course, an aggregated page doesn't need a source path
		super(AggregatedPage, self).__init__(name=name, source_path=source_path)

		self.aggregated_posts = aggregated_posts
		self.template = template

	def pprint(self, level=0):
		return "%sAggregatedPage(%s) [%s]" % (" "*level, self.title,
			",".join(p.name for p in self.aggregated_posts))


class Renderer(object):
	def __init__(self):
		pass

	def render(self, page):
		pass


class Jinja2Renderer(Renderer):
	def __init__(self, markup_processor, template_paths):
		super(Jinja2Renderer, self).__init__()

		self.markup_processor = markup_processor

		self.environment = jinja2.Environment(
			loader=jinja2.ChoiceLoader(
			[jinja2.FileSystemLoader(x) for x in template_paths]),
			autoescape=jinja2.select_autoescape())

	def render(self, page):
		# NOTE: We should accept some site information as an argument here as well
		# things like, title formatting, site navigation, etc.
		front_matter, content = self.markup_processor.process_source(page.source())

		template = self.environment.select_template(page.template)\
			if isinstance(page.template, list) else\
			self.environment.get_template(page.template)

		return template.render(front_matter=front_matter, content=content)

class Site(object):
	def __init__(self, name, directory, theme_path=None,
			content_relative_path="content", build_directory=None):
		self.name = name
		self.directory = Path(directory)
		self.content_path = self.directory / content_relative_path
		self.theme_path = theme_path
		self.build_directory = build_directory if build_directory\
			else self.directory / "build"

		self.content = None

		self.init_renderer()

	def build_content_tree(self):
		self.content = ContentTree.from_directory(self.content_path)

	def init_renderer(self):
		# This should be easily overwritten for any other render engine
		self.renderer = Jinja2Renderer(MarkdownMarkupProcessor(), [
			(self.theme_path / "templates") if self.theme_path else "",
			Path(__file__).parent / "default_theme"])

	def render(self, delete_old_directory_if_it_exists=True):
		if self.build_directory.exists():
			shutil.rmtree(self.build_directory)

		os.mkdir(self.build_directory)

		for leaf in self.content.leaves():
			path = self.build_directory / leaf.path()
			os.makedirs(path, exist_ok=True)

			with open(path / "index.html", "w") as f:
				f.write(self.renderer.render(leaf))


class MarkupProcessor(object):
	def __init__(self, front_matter_delimiter="+"):
		self.front_matter_delimiter = front_matter_delimiter

	def process_source(self, source):
		front_matter_source = ""
		content = ""
		writing_to_front_matter = False
		lines = source.splitlines()

		for i, line in enumerate(lines):
			if set(line) == set([self.front_matter_delimiter]):
				if writing_to_front_matter:
					content = "\n".join(lines[i+1:])
					break
				else:
					writing_to_front_matter = True
			else:
				front_matter_source += line + "\n"

		if writing_to_front_matter:
			# If we have any front matter
			return self.process_front_matter(front_matter_source), self.process_markup(content)
		else:
			return {}, self.process_markup(source)

	def process_front_matter(self, front_matter_source):
		front_matter = {}
		exec(front_matter_source, {}, front_matter)
		return front_matter

	def process_markup(self, source):
		raise NotImplementedError

class MarkdownMarkupProcessor(MarkupProcessor):
	def process_markup(self, source):
		return markdown.markdown(source)
