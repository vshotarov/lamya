import unittest

from .. import context # Add the path to pygeon to sys.path
import sys
from pathlib import Path
sys.path.append((Path(__file__).parent / "using_generator").__str__())

import using_generator


class TestUsingGenerator(unittest.TestCase):
	def test_using_generator(self):
		using_generator.build()
