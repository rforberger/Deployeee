try:
  from jinja2 import Environment, FileSystemLoader
  jinja2_package = True
except Exception as e:
  print(f"❌ Error cannot import jinja2 package: {e}")
  jinja2_package = None

import json

import yaml
import requests
from jsonschema import validate, ValidationError
try:
  from dotenv import load_dotenv
  # Load .env file
  #load_dotenv()
except Exception as e:
  print(f"Error loading env variables! {e}")
  sys.exit(3)



class CI:
  def __init__(self, config, deployeee, deploy):

    if jinja2_package:
      self.config = config
      self.deployeee = deployeee
      #print(self.config["deployment"]["ci"])
      if self.config["deployment"]["ci"] == "github":
        print(f"Building GitHub CI workflow..")

        run_engine = self.deployeee.get_config_value_by_section(self.config['containerrun'], key='runengine', environment=deploy.environment)

        runengines = self.config["runengines"]["runengines"]

        # application environment variables
        environment_variables = dotenv_values("container/app/.env")

        deploy_data = {
          "workflow": self.config["deployment"]["deployworkflow"],
          "data": {
            # "ENVS": [
            #   { "key": "FERNET_KEY", "value": "${{ secrets.fernet_key }}" },
            #   { "key": "PAYPAL_CLIENT_SECRET_ENCRYPTED", "value": "${{ secrets.paypal_client_secret_encrypted }}" }
            # ],
            "name": self.config['application']['name'],
            "description": self.config['application']['description'],
            "packages": self.config["install"]["packages"],
            "container_build_directory": self.config["containerbuild"]["containerdirectory"],
            "container_build_command": " ".join(deployeee.get_container_build_command("production")),
            "base_container_build_command": " ".join(deployeee.get_base_container_build_command("production", environment_variables)),
            "bicep_file": deployeee.get_json_from_config(runengines)[run_engine]["bicepfile"],
            "bicep_paramfile": deployeee.get_json_from_config(runengines)[run_engine]["bicepparamfile"],
            "manifest_deploy_type": deployeee.get_config_value_by_section(self.config['containerrun'], 'manifest_deploy_type', environment=deploy.environment),
            "platform": deployeee.get_json_from_config(runengines)[run_engine]["platform"],
            "cloud": deployeee.get_json_from_config(runengines)[run_engine]["cloud"],
            "deploytool": deployeee.get_json_from_config(runengines)[run_engine]["deploytool"],
            "rg": deployeee.get_json_from_config(runengines)[run_engine]["resourcegroup"],
            "buildsystem": self.config["containerbuild"]["buildsystem"]
          }
        }

        destroy_data = {
          "workflow": self.config["deployment"]["destroyworkflow"],
          "data": {
            "ENVS": []
          }
        }

        try:
          [self.create_workflow_from_deployment(workflow["workflow"], workflow["data"]) for workflow in (deploy_data, destroy_data)]
        except Exception as e:
          print(f"❌ Error creating workflow from deployment: {e}")

  def create_workflow_from_deployment(self, workflow, data):
    def print_ok(msg):
      print(f"✅ {workflow}: {msg}")

    def print_fail(msg):
      print(f"❌ {workflow}: {msg}")

    try:
      # Load the template from a directory
      env = Environment(loader=FileSystemLoader(self.config["deployment"]["template_dir"]))  # Current directory
    except Exception as e:
      print_ok(f"Error loading template from directory: {e}")

    try:
      template = env.get_template(workflow + ".yml.j2")
    except Exception as e:
      print_ok(f"Error building template: {e}")

    try:
      # Render the template
      rendered_content = template.render(data)
    except Exception as e:
      print_fail(f"Error rendering template: {e}")


    # Validate YAML syntax
    try:
      workflow_dict = yaml.safe_load(rendered_content)
      print_ok("YAML is valid!")
    except yaml.YAMLError as e:
      print_fail(f"YAML Syntax Error: {e}")
      exit(1)

    try:
      # Fetch GitHub Actions workflow JSON schema
      schema_url = "https://json.schemastore.org/github-workflow.json"
      schema = requests.get(schema_url).json()
    except Exception as e:
      print_fail(f"Cannot download GitHub Workflow schema: {e.message}")

    # Validate against GitHub Actions schema
    try:
      validate(instance=workflow_dict, schema=schema)
      print_ok("GitHub Workflow Schema is valid!")
    except ValidationError as e:
      print_fail(f"Schema Validation Error: {e.message}")

    try:
      # Save the rendered output to a file
      with open(".github/workflows/" + workflow + ".yml", "w") as f:
        f.write(rendered_content)
    except Exception as e:
      print_fail(f"Error writing github workflow: {e}")

  #def deploy(self):
  #  git push origin main