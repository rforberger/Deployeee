import requests
import base64
try:
  import nacl.encoding
  nacl_package = nacl.encoding
except Exception as e:
  nacl_package = None

try:
  import nacl.public
  nacl_package = nacl.public
except Exception as e:
  nacl_package = None

import os
import ast
import json

from .Config import *

class GitHub:
  def __init__(self, deployeee, GITHUB_SECRETS):
    if nacl_package:
      self.deployeee = deployeee
      # Set your GitHub details
      try:
        GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
      except Exception as e:
        print(f"Error loading env GITHUB_TOKEN: {e}")

      self.OWNER = self.deployeee.config['github']['owner']
      self.REPO = self.deployeee.config['github']['repo']

      # GitHub API Headers
      self.HEADERS = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
      }

      self.store_secrets(GITHUB_SECRETS)

  # Step 1: Get the Public Key
  def get_public_key(self):
    url = f"https://api.github.com/repos/{self.OWNER}/{self.REPO}/actions/secrets/public-key"
    response = requests.get(url, headers=self.HEADERS)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error getting public key: {response.text}")

  # Step 2: Encrypt the Secret
  def encrypt_secret(self, public_key: str, secret_value: str) -> str:
    public_key_bytes = base64.b64decode(public_key)
    public_key = nacl.public.PublicKey(public_key_bytes, nacl.encoding.RawEncoder)
    sealed_box = nacl.public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

  # Step 3: Store the Secret
  def store_secret_m(self, encrypted_value: str, key_id: str, SECRET_NAME):
    url = f"https://api.github.com/repos/{self.OWNER}/{self.REPO}/actions/secrets/{SECRET_NAME}"
    data = {
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }
    response = requests.put(url, headers=self.HEADERS, json=data)

    if response.status_code in [201, 204]:
      print(f"✅ Secret '{SECRET_NAME}' added successfully!")
    else:
      raise Exception(f"Error setting secret: {response.text}")

  def check_secret(self, encrypted_value, key_id, SECRET_NAME):
    """Check for secret"""
    url = f"https://api.github.com/repos/{self.OWNER}/{self.REPO}/actions/secrets/{SECRET_NAME}"

    payload = json.dumps({
      "encrypted_value": encrypted_value,
      "key_id": key_id
    })

    response = requests.get(url, headers=self.HEADERS, data=payload)

    if response.status_code in [200]:
      return True
    else:
      return False

  def create_secret(self, encrypted_value, key_id, SECRET_NAME):
    """Create or update the GitHub secret"""
    url = f"https://api.github.com/repos/{self.OWNER}/{self.REPO}/actions/secrets/{SECRET_NAME}"

    payload = json.dumps({
      "encrypted_value": encrypted_value,
      "key_id": key_id
    })

    response = requests.put(url, headers=self.HEADERS, data=payload)

    if response.status_code in [201, 204]:
      print("Secret created/updated successfully!")
    else:
      raise Exception(f"Failed to create/update secret: {response.text}")

  def store_secrets(self, GITHUB_SECRETS):
    # Run the script
    for SECRET_NAME, SECRET_VALUE in ast.literal_eval(GITHUB_SECRETS):
      try:
        key_data = self.get_public_key()
        encrypted_secret = self.encrypt_secret(key_data["key"], SECRET_VALUE)
        if not self.check_secret(encrypted_secret, key_data["key_id"], SECRET_NAME) == True:
          self.create_secret(encrypted_secret, key_data["key_id"], SECRET_NAME)
          self.store_secret_m(encrypted_secret, key_data["key_id"], SECRET_NAME)
      except Exception as e:
        print(f"❌ {e}")