from Deployeee.Deployeee import Deployeee
from Deployeee.Deploy import Deploy
from Deployeee.Setup import Setup
import sys




try:
  deployeee = Deployeee()
except Exception as e:
  print(f"Error instanciating Deployeee: {e}")
  sys.exit(3)

try:
  setup = Setup(debug = False)
except Exception as e:
  print(f"Error instantiating Setup: {e}")
  sys.exit(3)

try:
  deploy = Deploy(deployeee.config, deployeee.command_line_parameters, deployeee, debug = True)
except Exception as e:
  print(f"Error instanciating Deploy: {e}")
  sys.exit(3)


