import unittest

from .. import context # Add the path to pygeon to sys.path

import pygeon.main

class TestAllFullWebsites(unittest.TestCase):
	def test_simple_website(self):
		pygeon.main.build("personal_website",
			root_dir="tests/integration/personal_website/")

		# TODO: Compare the built website with a prebuilt ground truth version
