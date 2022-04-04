import unittest

from .. import context # Add the path to pygeon to sys.path

import pygeon.main

class TestShortcodes(unittest.TestCase):
	def test_simple_website(self):
		pygeon.main.build("shortcodes",
			root_dir="tests/integration/shortcodes/")

		# TODO: Compare the built website with a prebuilt ground truth version
