from pathlib import Path
import os
import markdown
from datetime import datetime
from copy import deepcopy
from collections import OrderedDict


class LeafChildError(Exception):
	pass

class PageOrPostWithoutSourceError(Exception):
	pass

def warning(*args):
	print("PygeonWarning:", *args)


class ContentTree:
	"""A tree implementation specific to parsing the content for a static website"""
	def __init__(self, name):
		super(ContentTree, self).__init__()
		self.name = name
		self._parent = None

	@property
	def parent(self):
		return self._parent

	@parent.setter
	def parent(self, _):
		raise AttributeError("'parent' can't be set directly. Use the "
			"'ContentTree.parent_to()' function.")

	def parent_to(self, new_parent):
		if not hasattr(new_parent, "children"):
			raise LeafChildError("{new_parent.name} does not accept children.")

		if self._parent:
			self._parent.children.remove(self)
		new_parent.children.append(self)
		self._parent = new_parent

	@property
	def path(self):
		return (self.parent.path / self.name) if self.parent else Path("/")

	@path.setter
	def path(self, _):
		raise AttributeError("'path' can't be set directly. It is managed internally.")

	def render_path(self, build_path):
		return Path(build_path) / (self.parent.path.relative_to("/")\
				if self.parent.index_page == self else self.path.relative_to("/"))\
				/ "index.html"

	@property
	def href(self):
		return self.parent.path if self.parent.index_page == self else self.path

	def pprint(self, level=0):
		return "{indent1}{type}({name})".format(indent1=" "*2*level,
				indent2=" "*2*(level+1), type=self.__class__.__name__, name=self.name)

	def __str__(self): return self.pprint()
	def __repr__(self): return self.pprint()

	@staticmethod
	def from_directory(directory):
		root = Root()

		def recursive_builder(parent, directory):
			for child_path in sorted(directory.iterdir()):
				if child_path.is_dir():
					child = recursive_builder(Folder(child_path.name), child_path)
					parent.add_child(child)

				elif child_path.stem == "index":
					child = CustomIndexPage(parent, source_path=child_path)
					parent.index_page = child

				else:
					child = PageOrPost(child_path.stem, source_path=child_path)
					parent.add_child(child)

			return parent

		recursive_builder(root, directory)

		return root


class Folder(ContentTree):
	"""Subtree"""
	def __init__(self, name):
		super(Folder, self).__init__(name)
		self._children = []
		self._index_page = None

	@property
	def children(self):
		return self._children

	@children.setter
	def children(self, _):
		raise AttributeError("'children' can't be set directly. Use the "
			"'ContentTree.parent_to()' function.")

	def add_child(self, child):
		child.parent_to(self)

	@property
	def index_page(self):
		return self._index_page

	@index_page.setter
	def index_page(self, new_index_page):
		self._index_page = new_index_page
		new_index_page._parent = self

	def pprint(self, level=0):
		return "{indent1}{type}({name}) {{\n{indent2}{children}\n{indent2}}}".format(
			indent1=" "*2*level, indent2=" "*2*(level+1), type=self.__class__.__name__,
			name=self.name, children=("\n" + " "*2*(level+1)).join(
				(["%si %s" % (" "*2*level, self.index_page.pprint(0))]\
					if self.index_page else []) +\
				 [x.pprint(level+1) for x in self.children]))

	def get(self, path):
		path = Path(path)
		path_parts = path.parts

		if not path_parts:
			return self

		first_part = path_parts[0]
		if first_part == "/":
			if len(path_parts) == 1:
				return self
			else:
				first_part = path_parts[1]
				path_parts = path_parts[1:]

		next_step = None
		for i,child in enumerate(self._children):
			if first_part in ["{%i}" % i, child.name]:
				next_step = child
				break

		if next_step:
			if isinstance(next_step, Folder):
				return next_step.get("/".join(path_parts[1:]))
			else:
				return next_step
		else:
			raise LookupError("The path '%s' does not exist under %s" % (path, self))

	def apply_func(self, func, include_index_pages=True, recursive=True):
		for child in self.children + ([self.index_page] if\
				self.index_page and include_index_pages else []):
			func(child)

			if isinstance(child, Folder) and recursive:
				child.apply_func(func, include_index_pages)

	def group(self, grouping_func, include_index_pages=True, recursive=True):
		grouped = {}
		for child in self.children + ([self.index_page] if\
				self.index_page and include_index_pages else []):
			grouped.setdefault(grouping_func(child), []).append(child)

			if isinstance(child, Folder) and recursive:
				for k,v in child.group(grouping_func, include_index_pages).items():
					existing_values = grouped.setdefault(k, [])
					existing_values += v

		return grouped

	def flat(self, include_index_pages=True):
		flattened = []
		for child in self.children:
			flattened.append(child)

			if isinstance(child, Folder):
				flattened += child.flat(include_index_pages)

		if include_index_pages and self.index_page:
			flattened.append(self.index_page)

		return flattened

	def leaves(self, include_index_pages=True):
		# NOTE: Should we return a 404 page or a ProceduralIndexPage if
		# include_index_pages is True and there's no include_index_pages
		# Or maybe an extra argument to specify that?
		return filter(lambda x: isinstance(x, AbstractPageOrPost),
			self.flat(include_index_pages))

	def filter(self, func, include_index_pages=True, recursive=True):
		copy = deepcopy(self)
		copy.filter_in_place(func, include_index_pages, recursive)

		return copy

	def filter_in_place(self, func, include_index_pages=True, recursive=True):
		to_remove = []

		for child in self.children:
			if isinstance(child, Folder):
				if recursive:
					child.filter_in_place(func, include_index_pages)
					if not func(child) and not child.children:
						to_remove.append(child)
				else:
					if not func(child):
						to_remove.append(child)
			elif not func(child):
				to_remove.append(child)

		for child in to_remove:
			self.children.remove(child)

		if include_index_pages and self.index_page and not func(self.index_page):
			self._index_page = None

	def as_dict(self, map_leaf=lambda x: x):
		return OrderedDict([
			(p.name, (p.as_dict(map_leaf)) if isinstance(p, Folder) and p.children\
				else map_leaf(p))\
			for p in self.children])


class Root(Folder):
	def __init__(self):
		super(Root, self).__init__("/")


class AbstractPageOrPost(ContentTree):
	"""Leaf"""
	def __init__(self, name, source_path=None, source=None):
		super(AbstractPageOrPost, self).__init__(name)
		self._source_path = source_path
		self._source = source

	@property
	def source_path(self):
		return self._source_path

	@source_path.setter
	def source_path(self, new_source_path):
		self._source_path = new_source_path
		if self._source:
			warning("The 'source_path' has been updated on %s, but"
				" the source has already been set, so the new 'source_path'"
				" will have no effect." % self.name)

	@property
	def source(self):
		if self._source is not None:
			return self._source
		elif self._source_path:
			with open(self._source_path, "r") as f:
				return f.read()
		else:
			raise PageOrPostWithoutSourceError("'%s' has neither 'source' nor"
				" 'source_path' defined." % self.name)

	@source.setter
	def source(self, new_source):
		self._source = new_source
		if self._source_path: warning("The 'source' has been updated on %s, but the"
				" 'source_path' has already been set, so the newly set 'source'"
				" will override that" % self.name)


class PageOrPost(AbstractPageOrPost):
	pass


class CustomIndexPage(PageOrPost):
	def __init__(self, parent, source_path=None, source=None):
		super(CustomIndexPage, self).__init__(parent.name, source_path, source)
		self._parent = parent


class ProceduralPage(AbstractPageOrPost):
	pass


class AggregatedPage(ProceduralPage):
	def __init__(self, name, aggregated_posts, source_path=None, source=None):
		super(AggregatedPage, self).__init__(name, source_path, source)
		self.aggregated_posts = aggregated_posts

	def pprint(self, level=0):
		return "%sAggregatedPage(%s) [%s]" % (" "*2*level, self.name,
			",".join(p.name for p in self.aggregated_posts))
