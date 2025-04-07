import tomllib
import argparse
import shutil
import json
import os
from .Config import *

config_file_path = "./deployeee.toml"

class Deployeee:
  def __init__(self):

    self.config = self.read_config()
    self.command_line_parameters = self.read_command_line_parameters()

  def __call__(self, *args, **kwargs):
    return self

  def read_config(self):
    with open(config_file_path, "rb") as f:
      config = tomllib.load(f)
    return config

  def read_command_line_parameters(self):
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description=self.config["application"]["description"])
    # Optional arguments
    #parser.add_argument("-l", "--local", action="store_true", help="Whether the application deploys to localhost or to the cloud")
    parser.add_argument("-d", "--development", action="store_true", help="Whether to use development mode on cloud deployment ")
    parser.add_argument("-p", "--production", action="store_true", help="Whether to use production mode on local build ")
    parser.add_argument("-r", "--run-local", action="store_true", help="Whether to run container locally")
    parser.add_argument("-c", "--deploy-cloud", action="store_true", help="Whether to deploy production to cloud")
    parser.add_argument("-du", "--dont-upload", action="store_true", help="Don't upload container")
    # Parse arguments
    args = parser.parse_args()
    return args

  def detect_command(self, command):
    '''Detects a command on Linux or MacOS'''
    try:
      return shutil.which(command)
    except Exception as e:
      print(f"Command not found: {e}")
      
  def get_config_value_by_section(self, config_value, key, environment):
    ret = {
      entry["environment"]: entry[key]
      for entry in config_value  if key in entry
    }.get(environment)
    return ret

  def get_image_name(self):
    return f"{self.config['containerbuild']['tag']}:{self.config['containerbuild']['containerbuildversion']}"

  def get_base_container_build_command(self, environment, environment_variables):
    try:
      build_command_base = [
        self.config["containerbuild"]["buildsystem"],
        "build",
        "-t",
        f"{self.config['application']['name'].lower()}_base:latest",
        "-f",
        "Containerfile.base"
      ]
    except Exception as e:
      print(f"Error building build command base: {e}")

    try:
      # Your environment variables formatted as --env key=value pairs
      #env_params = [item for sublist in [[f"--env", f"{key}={value}"] for item in environment_variables for key, value in item.items()] for item in sublist]
      # Build the list dynamically
      env_params = []
      for key, value in environment_variables.items():
        env_params.extend(["--env", f"{key}={value}"])
      # Extend the build_command_base with env_params
      build_command_base.extend(env_params)
    except Exception as e:
      print(f"Error building env parameters: {e}")

    return build_command_base

  def get_container_build_command(self, environment):
    try:
      build_command = self.config["containerbuild"]["buildsystem"]
      '''TODO: Construct buildsystem args'''
      image_name = self.get_image_name()

      #ports = [f" ,{port}" for port in (self.get_config_value_by_section(["containerrun"]["published_ports"], environment))]
      ports=self.get_config_value_by_section(self.config['containerrun'], 'published_ports', environment)

      build_system_args = [
         build_command,
         "build",
         "-t",
         image_name,
         "-f",
         f"{self.config['containerbuild']['containerfile']}",
         f"--build-arg", f"environment={environment}",
         f"--build-arg", f"base_url={self.get_config_value_by_section(self.config['hosting'], 'base_url', environment)}",
         f"--build-arg", f"exposed_ports={ports}",
         f"--cpu-shares", f"4096",
         "."
       ]
      return build_system_args
    except Exception as e:
      print(f"Could not build container build command: {e}")


  def get_json_from_config(self, json_str):
    # Parse the JSON string using json.loads()
    try:
      json_data = json.loads(json_str)
      return json_data
    except json.JSONDecodeError as e:
      print("Error parsing JSON:", e)