import unittest

from .. import context # Add the path to pygeon to sys.path

import pygeon.main

class TestSimpleWebsite(unittest.TestCase):
	def test_simple_website(self):
		pygeon.main.build("simple_website",
			root_dir="tests/integration/simple_website/")

		# TODO: Compare the built website with a prebuilt ground truth version
