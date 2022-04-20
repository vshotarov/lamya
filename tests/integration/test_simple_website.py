import unittest

from .. import context # Add the path to pygeon to sys.path
import sys
from pathlib import Path
sys.path.append((Path(__file__).parent / "simple_website").__str__())

import simple_website


class TestSimpleWebsite(unittest.TestCase):
	def test_simple_website(self):
		simple_website.build()
