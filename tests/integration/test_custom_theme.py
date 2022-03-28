import unittest

from .. import context # Add the path to pygeon to sys.path

import pygeon.main

class TestCustomTheme(unittest.TestCase):
	def test_simple_website(self):
		pygeon.main.build("custom_theme",
			root_dir="tests/integration/custom_theme/")

		# TODO: Compare the built website with a prebuilt ground truth version
