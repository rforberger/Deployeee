import sys

try:
  from dotenv import load_dotenv
  # Load .env file
  load_dotenv()
except Exception as e:
  print(f"Error loading env variables! {e}")
  sys.exit(3)
