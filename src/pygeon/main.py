from pathlib import Path
import os
import markdown
from datetime import datetime
from copy import deepcopy


class ContentTree(object):
	def __init__(self, name, parent, real_path):
		self.name = name
		self._parent = parent
		self._real_path = real_path

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
		self.children.append(child)

	def remove_child(self, child):
		self.children.remove(child)
	
	@property
	def real_path(self):
		return self._real_path

	@real_path.setter
	def real_path(self, new_real_path):
		self._real_path = new_real_path
	
	def pprint(self, level=0):
		return "%s%s(%s) {\n%s%s\n%s}" % (" "*level, self.__class__.__name__,
			self.name, " "*(level+1),
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
		root = Root("Content", Path(directory))

		def recursive_builder(parent):
			for child_path in sorted(parent.real_path.iterdir()):
				child = recursive_builder(ContentTree(child_path.name, parent, child_path))\
					if child_path.is_dir() else Leaf(child_path.stem, parent, child_path)
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
			setattr(x, "name", x.name.replace("_"," ").title())):
		self.map_in_place(title_func)

class Root(ContentTree):
	def __init__(self, name, real_path):
		super(Root, self).__init__(name=name, parent=None, real_path=real_path)

class Leaf(ContentTree):
	def __init__(self, name, parent, real_path):
		super(Leaf, self).__init__(name=name, parent=parent, real_path=real_path)
	
	@property
	def children(self):
		raise AttributeError("Leaf nodes can't have children")

	@children.setter
	def children(self, _):
		raise AttributeError("Leaf nodes can't have children")
	
	def pprint(self, level=0):
		return "%sLeaf(%s)" % (" "*level, self.name)
