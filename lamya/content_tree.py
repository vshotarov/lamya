"""The :mod:`lamya.content_tree` module provides a naive tree data structure
implementation, specifically designed to serve as a base for generating
static sites. The :mod:`lamya.site_generator` module utilises this to provide
a static site generator, but users are also encouraged to write their own
build scripts directly using the :mod:`lamya.content_tree` module.
"""
from pathlib import Path
from copy import deepcopy
from collections import OrderedDict
from math import ceil

try:
    import markdown
except ImportError:
    markdown = None

from lamya.content_processing import split_front_matter


class ContentTree:
    """A tree implementation specific to parsing, modifying and generating
    the content for a static website.

    This is the abstract base class.

    :param name: the name of the node
    :param user_data: a convenience object for storing custom user data
    :param parent: a handle to the parent node
    :param ancestors: a list of all the ancestors starting from the direct parent
    :param path: a `pathlib.Path` object containing the path to this node starting
        from the root
    :param href: a `pathlib.Path` object containing the path to this node,
        corresponding to what's deemed the correct way referencing the path as a URL
    """
    def __init__(self, name, user_data=None):
        """Constructor

        :param name: the name of the node
        :param user_data: a convenience object for storing custom user data
        """
        super().__init__()
        self.name = name
        self._parent = None
        self.user_data = user_data if not user_data is None else {}

    @property
    def parent(self):
        """Get the parent of the node."""
        return self._parent

    @parent.setter
    def parent(self, _): # pylint: disable=no-self-use
        raise AttributeError("'parent' can't be set directly. Use the "
            "'ContentTree.parent_to()' function.")

    def parent_to(self, new_parent):
        """Parent this node to the `new_parent`.

        :param new_parent: the new parent to parent this node to"""
        if not hasattr(new_parent, "children"):
            raise LeafChildError("{new_parent.name} does not accept children.")

        if self._parent:
            self._parent.children.remove(self)
        new_parent.children.append(self)
        self._parent = new_parent

    @property
    def ancestors(self):
        """Get a list of ancestors, starting with the direct parent."""
        _ancestors = []
        p = self
        while p.parent:
            _ancestors.append(p.parent)
            p = p.parent
        return _ancestors

    @property
    def path(self):
        """Get the path of this node relative to the root."""
        return (self.parent.path / self.name)\
            if self.parent else Path("/")

    @path.setter
    def path(self, _): # pylint: disable=no-self-use
        raise AttributeError("'path' can't be set directly. It is managed internally.")

    @property
    def href(self):
        """Returns the path of this node relative to the root, but only if this
        node is not an `index_page` to another node, in which case it returns
        the path of that node instead.

        This corresponds to the fact that in the context of static websites
        the `index.html` page of a folder is in a path like
        `{..}/folder/index.html` and not `{..}/folder/folder/index.html`.
        """
        return self.parent.path if getattr(self, "is_index_page", lambda: False)()\
            else self.path

    def pprint(self, level=0):
        """Returns a pretty string displaying information about this node.

        :param level: the indentation level, so we support nesting"""
        return "{indent1}{type}({name})".format( # pylint: disable=consider-using-f-string
            indent1=" "*2*level, type=self.__class__.__name__, name=self.name)

    def __str__(self):
        return self.pprint()
    def __repr__(self):
        return self.pprint()

    @staticmethod
    def from_directory(directory, accepted_file_types=None, post_create_callback=None):
        """Builds a :class:`ContentTree` structure by walking a directory.

        :param directory: the directory to walk, which would usually be the
            content folder of a static website
        :param accepted_file_types: a list of accepted file extensions. Defaults
            to markdown files only
        :param post_create_callback: a function to be called after each node
            of the content tree is created. Defaults to None"""
        post_create_callback = post_create_callback or (lambda _: None)
        root = Root()
        post_create_callback(root)

        def recursive_builder(parent, directory):
            for child_path in sorted(directory.iterdir()):
                if child_path.is_dir():
                    child = recursive_builder(Folder(child_path.name), child_path)
                    parent.add_child(child)

                elif child_path.suffix not in (accepted_file_types\
                        if accepted_file_types is not None else [".md"]):
                    continue

                elif child_path.stem == "index":
                    child = CustomIndexPage(parent, source_path=child_path)
                    parent.index_page = child

                else:
                    child = PageOrPost(child_path.stem, source_path=child_path)
                    parent.add_child(child)

                post_create_callback(child)

            return parent

        recursive_builder(root, directory)

        return root


class Folder(ContentTree):
    """This class represents a subtree, or in the context of a static website
    a group/folder with pages or groups/folders underneath it.

    You can think of it as the `blog` folder which is the parent to all the
    blog posts in a hypothetical personal website.

    :param children: a list of all the direct children of this node
    :param index_page: the index_page node of this folder. If we follow the
        example of a `blog` folder, the index page is most likely a list of
        all the blog posts
    """
    def __init__(self, name, user_data=None):
        """Constructor

        :param name: the name of the node
        :param user_data: a convenience object for storing custom user data
        """
        super().__init__(name, user_data)
        self._children = []
        self._index_page = None

    @property
    def children(self):
        """Returns a list of all the direct children of this node."""
        return self._children

    @children.setter
    def children(self, _): # pylint: disable=no-self-use
        raise AttributeError("'children' can't be set directly. Use the "
            "'ContentTree.parent_to()' function.")

    def add_child(self, child):
        """Adds a child to this node and unparents it from its previous parent.

        :param child: the child to be parented to this node"""
        child.parent_to(self)

    @property
    def index_page(self):
        """The index page of this folder"""
        return self._index_page

    @index_page.setter
    def index_page(self, new_index_page):
        """Sets the index page of the this folder.

        :param new_index_page: the new index page to set
        """
        if new_index_page.parent:
            if new_index_page.is_index_page():
                new_index_page.parent.index_page = None
            else:
                new_index_page.parent.children.remove(new_index_page)
        self._index_page = new_index_page
        new_index_page._parent = self # pylint: disable=protected-access

    @property
    def path(self):
        """Get the path of this node relative to the root."""
        return super().path

    def pprint(self, level=0):
        """Returns a pretty string displaying information about this node.

        :param level: the indentation level, so we support nesting"""
        return "{indent1}{type}({name}) {{\n{indent2}{children}\n{indent2}}}".format( # pylint: disable=consider-using-f-string
            indent1=" "*2*level, indent2=" "*2*(level+1), type=self.__class__.__name__,
            name=self.name, children=("\n" + " "*2*(level+1)).join(
                (["%si %s" % (" "*2*level, self.index_page.pprint(0))] # pylint: disable=consider-using-f-string
                    if self.index_page else []) +\
                 [x.pprint(level+1) for x in self.children]))

    def get(self, path):
        """Gets a descendant of this node by a path.

        :param path: a path, relative to this node, to the desired descendant

        :raises LookupError: if the path does not exist under this node
        """
        path = Path(path)
        path_parts = path.parts

        if not path_parts:
            return self

        first_part = path_parts[0]
        if first_part == "/":
            if len(path_parts) == 1:
                return self
            first_part = path_parts[1]
            path_parts = path_parts[1:]

        next_step = None
        for i,child in enumerate(self._children):
            if first_part in [f"{{{i}}}", child.name] + (
                    [f"page{int(child.pagination.page_number)}"]\
                    if isinstance(child, PaginatedAggregatedPage) else []):
                next_step = child
                break

        if next_step:
            if isinstance(next_step, Folder):
                return next_step.get("/".join(path_parts[1:]))
            return next_step
        raise LookupError(f"The path '{path}' does not exist under {self}")

    def apply_func(self, func, include_index_pages=True, recursive=True):
        """Applies a function to all nodes in this subtree.

        :param func: the function to be applied
        :param include_index_pages: whether to apply the function to index pages
            Default is True
        :param recursive: whether to apply the function to all descendants or
            just the direct children. Default is True (all descendants)
        """
        for child in list(self.children) + ([self.index_page] if\
                self.index_page and include_index_pages else []):
            func(child)

            if isinstance(child, Folder) and recursive:
                child.apply_func(func, include_index_pages)

    def to_groups(self, grouping_func, include_index_pages=True, recursive=True,
            filter_func=lambda x: True):
        """Sorts the descendants of this subtree into one or more groups, based
        on the return value of a grouping function.

        :param grouping_func: the function to group nodes by. It accepts a node
            and should return a string specifying the group to put the node in
        :param include_index_pages: whether to apply the function to index pages.
            Default is True
        :param recursive: whether to apply the function to all descendants or
            just the direct children. Default is True (all descendants)
        :param filter_func: optional function to use as a filter
        """
        grouped = {}
        for child in list(self.children) + ([self.index_page] if\
                self.index_page and include_index_pages else []):
            if filter_func(child):
                grouped.setdefault(grouping_func(child), []).append(child)

            if isinstance(child, Folder) and recursive:
                for k,v in child.to_groups(grouping_func, include_index_pages,
                        filter_func=filter_func).items():
                    existing_values = grouped.setdefault(k, [])
                    existing_values += v

        return grouped

    def flat(self, include_index_pages=True):
        """Returns a one dimensional list of all descendants.

        :param include_index_pages: whether to apply the function to index pages.
            Default is True
        """
        flattened = []
        for child in self.children:
            flattened.append(child)

            if isinstance(child, Folder):
                flattened += child.flat(include_index_pages)

        if include_index_pages and self.index_page:
            flattened.append(self.index_page)

        return flattened

    def leaves(self, include_index_pages=True):
        """Returns all the leaf nodes (pages or posts) in this subtree.

        :param include_index_pages: whether to apply the function to index pages.
            Default is True
        """
        return list(filter(lambda x: isinstance(x, AbstractPageOrPost),
            self.flat(include_index_pages)))

    def filter(self, func, include_index_pages=True, recursive=True):
        """Returns a copy of this subtree with nodes filtered by the `func` arg.

        :param func: the filter function
        :param include_index_pages: whether to apply the function to index pages.
            Default is True
        :param recursive: whether to apply the function to all descendants or
            just the direct children. Default is True (all descendants)
        """
        copy = deepcopy(self)
        copy.filter_in_place(func, include_index_pages, recursive)

        return copy

    def filter_in_place(self, func, include_index_pages=True, recursive=True):
        """Filters nodes in this subtree by the `func` arg.

        :param func: the filter function
        :param include_index_pages: whether to apply the function to index pages.
            Default is True
        :param recursive: whether to apply the function to all descendants or
            just the direct children. Default is True (all descendants)
        """
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

    def group(self, name, entities):
        """Groups the specified `entities` into a new folder inside of this
        folder.

        :param name: name of the new folder
        :param entities: a list of ContentTree entities to group under the
            new parent

        :raises GroupError: if the list of entities is empty
        """
        if not entities:
            raise GroupError("Can't group an empty list of entities")

        group = Folder(name)
        group.parent_to(self)

        for entity in entities:
            entity.parent_to(group)

        return group

    def as_dict(self, map_leaf=lambda x: x, map_folder=lambda x: x):
        """Returns a `dict` representing this subtree, with leaves and folders
        optionally remapped by mapping functions.

        :param map_leaf: the function to remap leaf nodes with
        :param map_folder: the function to remap folder nodes with
        """
        return OrderedDict([
            (p.name,
             {"self": map_folder(p), "children": (p.as_dict(map_leaf,map_folder))}\
                if isinstance(p, Folder) and p.children else\
             map_leaf(p))\
            for p in self.children])


class Root(Folder):
    """The root of a content tree structure. The only difference with a regular
    folder is that the name is hardcoded to "/".
    """
    def __init__(self, user_data=None):
        """Constructor

        :param user_data: a convenience object for storing custom user data
        """
        super().__init__("/", user_data)


class AbstractPageOrPost(ContentTree):
    """This is the base leaf node of the content tree, which in the context
    of a static website represents a post or a page.

    :param source_path: path to an optional corresponding source path
    :param source: the source for this page or post. Either the source or
        the source_path need to be set on anything except for `Aggregated[Groups]Pages`,
        if the source is ever going to be requested, otherwise an error will be raised.
    :param front_matter: if the front matter has been parsed this is a `dict`
        containing the front matter evaluated from the source
    :param raw_content: this is the raw content of the source, meaning not yet
        processed by any markup processor
    :param content: this is the markup processed content
    """
    def __init__(self, name, source_path=None, source=None, user_data=None):
        """Constructor

        :param name: name of this node
        :param source_path: an optional path to a source file
        :param source: optional source of this node
        :param user_data: a convenience object for storing custom user data
        """
        super().__init__(name, user_data)
        self._source_path = source_path
        self._source = source

        self._front_matter = None
        self._raw_content = None
        self._content = None

    @property
    def source_path(self):
        """Returns the path to the source of this node"""
        return self._source_path

    @source_path.setter
    def source_path(self, new_source_path):
        """Sets the path to the source of this node."""
        self._source_path = new_source_path
        if self._source:
            warning(f"The 'source_path' has been updated on {self.name}, but"
                " the source has already been set, so the new 'source_path'"
                " will have no effect.")

    @property
    def source(self):
        """Gets the source of this node. If the `source` has been directly set
        or read from the `source_path` then that's returned. Otherwise, an
        attempt is made to read the source from the `source_path` and if that
        fails a :exc:`PageOrPostWithoutSourceError` is raised.

        :raises PageOrPostWithoutSourceError: if no source can be identified"""
        if self._source is not None:
            return self._source
        if self._source_path:
            with open(self._source_path, "r", encoding="utf-8") as f:
                return f.read()
        raise PageOrPostWithoutSourceError(
            f"'{self.name}' has neither 'source' nor 'source_path' defined.")

    @source.setter
    def source(self, new_source):
        """Sets the `source` of this node directly. If the `source_path` is also
        set, a warning is raised, since the `source` takes precedence over that.

        :param new_source: the new source to set
        """
        self._source = new_source
        if self._source_path:
            warning(f"The 'source' has been updated on {self.name}, but the"
                " 'source_path' has already been set, so the newly set 'source'"
                " will override that")

    def render_path(self, build_path):
        """Get the path of this node relative to the root and append it to the
        `build_path` argument and adding `index.html` at the end.

        :param build_path: a `pathlib.Path` object specifying the path to append
            the current path of the node to
        """
        return Path(build_path) / (self.parent.path.relative_to("/")\
                if self.parent and hasattr(self, "is_index_page") and self.is_index_page()\
                    else self.path.relative_to("/")) / "index.html"

    def is_index_page(self):
        """Returns whether or not this page or post is the index page of its parent"""
        return False if not self.parent else self.parent.index_page == self

    @property
    def front_matter(self):
        """If the front matter has already been parsed, returns a `dict` containing
        it, otherwise returns None and prints a warning."""
        if self._front_matter is None:
            warning(f"'front_matter' was requested on {self.name}, but it's not been "
                "read and parsed yet. Use 'parse_front_matter_and_content()' first")
        return self._front_matter

    @property
    def raw_content(self):
        """If the content has been parsed, returns it raw as taken from the source,
        otherwise returns None and prints a warning"""
        if self._raw_content is None:
            warning(f"'raw_content' was requested on {self.name}, but it's not been "
                "read and parsed yet. Use 'parse_front_matter_and_content()' first")
        return self._raw_content

    @property
    def content(self):
        """If the content has been parsed, returns it processed by the markup
        processor, otherwise returns None and prints a warning."""
        if self._content is None:
            warning(f"'content' was requested on {self.name}, but it's not been "
                "generated yet. Use 'process_content()' first")
        return self._content

    def parse_front_matter_and_content(self,
            front_matter_and_content_split_func = split_front_matter):
        """Takes the source and splits its front matter from its content, storing
        them in `self._front_matter` and `self._raw_content` respectively.

        :param front_matter_and_content_split_func: the function to use for
            splitting the front matter from the content. By default uses the
            :func:`lamya.content_processing.split_front_matter` function.
        """
        self._front_matter, self._raw_content =\
            front_matter_and_content_split_func(self.source)

    def process_content(self,
            markup_processor_func=markdown.markdown if markdown else None):
        """Processes the `raw_content` using the `markup_processor_func`.

        :param markup_processor_func: the function to process the `raw_content`
            with in order to produce the final content. By default it attempts
            to use the `markdown.markdown` function if `markdown` is available.
        """
        self._content = markup_processor_func(self._raw_content or "")


class PageOrPost(AbstractPageOrPost):
    """Giving a more explicit name to the class used for specific pages and posts."""


class CustomIndexPage(PageOrPost):
    """The class used for index pages that have been read from an index file,
    rather than procedurally generated."""
    def __init__(self, parent, source_path=None, source=None, user_data=None):
        """Constructor

        :param parent: the parent this page is the index of
        :param source_path: an optional path to a source file
        :param source: optional source of this node
        :param user_data: a convenience object for storing custom user data
        """
        super().__init__(
            parent.name, source_path, source, user_data)
        self.parent_to(parent)


class ProceduralPage(AbstractPageOrPost):
    """The base class for procedurally generated content tree pages.

    :param source: the difference with the :attr:`AbstractPageOrPost.source` property
        is that on :class:`ProceduralPage`s it is not required to have a `source`
        or `source_path` defined, while one of them is required for an
        :class:`AbstractPageOrPost`."""
    @property
    def source(self):
        if self._source is not None:
            return self._source
        if self._source_path:
            with open(self._source_path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    @source.setter
    def source(self, new_source):
        """Sets the `source` of this node directly. If the `source_path` is also
        set, a warning is raised, since the `source` takes precedence over that.

        :param new_source: the new source to set
        """
        self._source = new_source
        if self._source_path:
            warning(f"The 'source' has been updated on {self.name}, but the"
                " 'source_path' has already been set, so the newly set 'source'"
                " will override that")


class AggregatedGroupsPage(ProceduralPage):
    """A procedurally generated page containing groups of posts, a great example
    of which is categories and archives.
    """
    def __init__(self, name, aggregated_grouped_posts, source_path=None, # pylint: disable=too-many-arguments
            source=None, user_data=None):
        """Constructor

        :param name: name of this node
        :param aggregated_grouped_posts: a `dict` with the group names for keys and
            the corresponding lists of posts as the values
        :param source_path: an optional path to a source file
        :param source: optional source of this node
        :param user_data: a convenience object for storing custom user data
        """
        super().__init__(
            name, source_path, source, user_data)
        self.aggregated_grouped_posts = aggregated_grouped_posts

    def pprint(self, level=0):
        """Returns a pretty string displaying information about this node.

        :param level: the indentation level, so we support nesting"""
        return "%sAggregatedGroupsPage(%s) {%s}" % ( # pylint: disable=consider-using-f-string
            " "*2*level, self.name,
            ", ".join(k + ": " + ",".join(p.name for p in v)\
            for k,v in self.aggregated_grouped_posts.items()))


class AggregatedPage(ProceduralPage):
    """A procedurally generated page containing a list of posts."""
    def __init__(self, name, aggregated_posts, source_path=None, # pylint: disable=too-many-arguments
            source=None, user_data=None):
        """Constructor

        :param name: name of this node
        :param aggregated_posts: a list of posts
        :param source_path: an optional path to a source file
        :param source: optional source of this node
        :param user_data: a convenience object for storing custom user data
        """
        super().__init__(name, source_path, source, user_data)
        self.aggregated_posts = aggregated_posts

    def pprint(self, level=0):
        """Returns a pretty string displaying information about this node.

        :param level: the indentation level, so we support nesting"""
        return "%sAggregatedPage(%s) [%s]" % ( # pylint: disable=consider-using-f-string
            " "*2*level, self.name,
            ",".join(p.name for p in self.aggregated_posts))

    def paginate(self, num_posts_per_page, post_create_callback=lambda _: None):
        """Splits this page into multiple pages.

        :param num_posts_per_page: number of posts per page
        :param post_create_callback: a function to call on each generated page,
            after its creation
        """
        if num_posts_per_page <= 0:
            raise PaginationError("Can't paginate with less than 1 posts per page")

        pages = []
        for i in range(0, len(self.aggregated_posts), num_posts_per_page):
            pages.append(PaginatedAggregatedPage(
                self.name,self.aggregated_posts[i:i+num_posts_per_page],
                Pagination(i/num_posts_per_page+1,
                    ceil(len(self.aggregated_posts) / num_posts_per_page),
                    None, None, prev_page=None if i == 0 else pages[-1]),
                source_path=self.source_path, source=self._source))
            post_create_callback(pages[-1])
            pages[-1]._front_matter = self._front_matter # pylint: disable=protected-access
            pages[-1]._raw_content = self._raw_content # pylint: disable=protected-access
            pages[-1]._content = self._content # pylint: disable=protected-access
            pages[-1].user_data = dict(self.user_data)

            if len(pages) > 1:
                pages[-2].pagination.next_page = pages[-1]

        for p in pages:
            p.pagination.first_page = pages[0]
            p.pagination.last_page = pages[-1]

        if self.is_index_page():
            self.parent.index_page = pages[0]
            for p in pages[1:]:
                p.parent_to(self.parent)
        else:
            for p in pages:
                p.parent_to(self.parent)
            self.parent.children.remove(self)

        return pages


class PaginatedAggregatedPage(AggregatedPage):
    """A paginated version of the `AggregatedPage` containing only a subset of
    all the posts belonging to the `AggregatedPage` this page was derived from."""
    def __init__(self, name, aggregated_posts, pagination, # pylint: disable=too-many-arguments
            source_path=None, source=None, user_data=None):
        """Constructor

        :param name: name of this node
        :param aggregated_posts: a list of posts
        :param pagination: the :class:`Pagination` object managing this page
        :param source_path: an optional path to a source file
        :param source: optional source of this node
        """
        super().__init__(
            name, aggregated_posts, source_path, source, user_data=None)
        self.pagination = pagination

    def pprint(self, level=0):
        """Returns a pretty string displaying information about this node.

        :param level: the indentation level, so we support nesting"""
        return "%sPaginatedAggregatedPage(%s, %i) [%s]" % ( # pylint: disable=consider-using-f-string\
            " "*2*level, self.name, self.pagination.page_number,
            ",".join(p.name for p in self.aggregated_posts))

    def paginate(self, *args):
        """Attempting to paginated a :class:`PaginatedPage` will raise a :exc:`PaginationError`

        :raises PaginationError:
        """
        raise PaginationError(f"The page '{self.name}' is already paginated.")

    @property
    def path(self):
        """Gets the path of this page.

        This is slightly different since we have 2 extra rules:
        - if the index page of the parent is one of the pages belonging to the
        same pagination object this page does, then we return `{parent_path}/page%%i` "
        - if there's only one page we return an unpaginated path
        """
        if self.pagination.first_page.is_index_page():
            return self.parent.path /\
                (f"page{int(self.pagination.page_number)}")
        if self.pagination.max_page_number == 1:
            return self.parent.path / self.name
        return self.parent.path / self.name /\
            (f"page{int(self.pagination.page_number)}")


class Pagination: # pylint: disable=too-few-public-methods
    """A data struct containing all the information for a paginated aggregated
    page.

    We need an object like this, as the paginated pages are separate pages
    which don't store references to each other.

    :param page_number: the page number corresponding to the page this pagination
        instance belongs to
    :param max_page_number: the last page number
    :param first_page: a reference to the first page in the pagination
    :param last_page: a reference to the last page in the pagination
    :param prev_page: a reference to the prev page in the pagination
    :param next_page: a reference to the next page in the pagination
    """
    def __init__(self, page_number, max_page_number, first_page, last_page, # pylint: disable=too-many-arguments
            prev_page=None, next_page=None):
        self.page_number = page_number
        self.max_page_number = max_page_number
        self.first_page = first_page
        self.last_page = last_page
        self.prev_page = prev_page
        self.next_page = next_page

    def as_navigation_dict(self):
        """Returns a representation of this pagination object as a dictionary
        containing all the information necessary to correctly display a navigation
        structure inside an html template.
        """
        root = str(self.last_page.href).replace(
            f"page{(self.max_page_number)}", "").rstrip("/")
        return {
            "page_number" : self.page_number,
            "max_page_number" : self.max_page_number,
            "first_page_href" : str(self.first_page.href),
            "last_page_href" : str(self.last_page.href),
            "prev_page_href" : str(self.prev_page.href) if self.prev_page else None,
            "next_page_href" : str(self.next_page.href) if self.next_page else None,
            "root": root if root else "/"
        }


class LeafChildError(Exception):
    """An error specifiyng attempted access to the child/subtree of a leaf node"""

class PageOrPostWithoutSourceError(Exception):
    """An error specifiyng attempted access to the source code of a node which
    has none specified neither with a `source_path` nor directly set."""

class PaginationError(Exception):
    """An error when attempting to paginate an `AggregatedPage`, which can be
    triggered due to either not having any posts to paginate OR attempting to
    paginate an already paginated page."""

class GroupError(Exception):
    """An error raised when attempting to group an empty list of items into a subtree."""

def warning(*args):
    """A utility function for displaying warnings.

    The `*args` are directly passed into a print statement.
    """
    print("LamyaWarning:", *args)
