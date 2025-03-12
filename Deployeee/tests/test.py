import unittest
from Deployeee.Deployeee import Deployeee

class TestDeployeee(unittest.TestCase):
  def setUp(self):
    self.D = Deployeee()
  def test_Deployeee(self):
    config = self.D.read_config()
    self.assertEqual(isinstance(config, dict), True)