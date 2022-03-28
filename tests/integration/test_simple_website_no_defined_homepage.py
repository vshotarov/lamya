import unittest

from .. import context # Add the path to pygeon to sys.path

import pygeon.main

class TestSimpleWebsiteNoDefinedHomepage(unittest.TestCase):
	def test_simple_website(self):
		pygeon.main.build("simple_website_no_defined_homepage",
			root_dir="tests/integration/simple_website_no_defined_homepage/")

		# TODO: Compare the built website with a prebuilt ground truth version
