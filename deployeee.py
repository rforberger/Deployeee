#!/usr/bin/env python3
import sys

def is_venv():
  # Using sys.base_prefix (Python 3.8+)
  if hasattr(sys, 'base_prefix'):
    return sys.base_prefix != sys.prefix
  else:
    # For Python versions prior to 3.8
    return hasattr(sys, 'real_prefix')

# Test for venv
if not is_venv():
  print(f"Not in a venv")
  sys.exit(2)

from Deployeee import Deployeee

deployeee_app = Deployeee()
