import subprocess
from .CI import CI
import os
import sys
from .GitHub import GitHub
try:
  from alive_progress import alive_bar
  alive_progress_package = alive_bar
except ImportError:
  alive_progress_package = None
import time
import json
import base64

try:
  from dotenv import dotenv_values, load_dotenv
  # Load .env file
  #load_dotenv()
except Exception as e:
  print(f"Error loading env variables! {e}")
  sys.exit(3)

class Deploy:
  def __init__(self, config, command_line_parameters, deployeee, debug = True):
    self.config = config
    self.deployeee = deployeee
    self.command_line_parameters = command_line_parameters
    self.environment = "development"
    self.debug = debug

    # decide what to run
    if self.command_line_parameters.deploy_cloud and not self.command_line_parameters.development:
      self.environment = "production"
      # Store GitHub
      self.store_github()
      self.deploy_cloud()
    #elif self.command_line_parameters.deploy_cloud and self.command_line_parameters.development:
      # Store GitHub
      #self.store_github()
      #self.deploy_cloud()
    elif self.command_line_parameters.run_local and not self.command_line_parameters.development and not self.command_line_parameters.deploy_cloud:
      self.run_local()
    elif not self.command_line_parameters.development and not self.command_line_parameters.deploy_cloud and self.command_line_parameters.production:
      self.environment = "production"
      # Check if deploy system is running
      if self.config["containerbuild"]["buildsystem"] == "podman":
        if self.test_podman():
          self.deploy_local()
    elif not self.command_line_parameters.development and not self.command_line_parameters.deploy_cloud:
      # Check if deploy system is running
      if self.config["containerbuild"]["buildsystem"] == "podman":
        if self.test_podman():
          self.deploy_local()

    else:
      print("Unknown parameters submitted")

    # Exit cleanly
    sys.exit(0)

  def __call__(self, *args, **kwargs):
    return self

  def test_podman(self):
    print(f"Testing if podman is running...")
    try:
      result = subprocess.run(["podman", "info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
      if result.returncode == 0:
        print("OK")
        return True # Return True if command succeeds
      else:
        print("No.")
        return False
    except FileNotFoundError as e:
      print (f"Not installed, Error: {e}")
      return False

  # def container_build_local(self):
  #   try:
  #     build_system_args = self.deployeee.get_container_build_command(self.environment)
  #     #result = subprocess.run(build_system_args, capture_output=True, text=True, cwd=self.config["containerbuild"]["containerdirectory"])
  #     process = subprocess.Popen(build_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=self.config["containerbuild"]["containerdirectory"])
  #
  #     if self.debug = True:
  #     # Read and print output line by line
  #       for line_stdout in iter(process.stdout.readline, ''):
  #         print(line_stdout, end="")  # `end=""` prevents double newlines
  #     else:
  #       print("Building container ...")
  #
  #     image_name = self.deployeee.get_image_name()
  #     #print(result.stdout)
  #     #print(result.stderr)
  #     return image_name
  #   except FileNotFoundError:
  #     print("The specified directory does not exist.")
  #   except subprocess.CalledProcessError as e:
  #     print(f"Command failed: {e}")
  #   except Exception as e:
  #     print(f"Error building local container: {e}")

  #def read_and_print_output_by_line(self, process, text, debug):


  def build_container(self, build_command):
    try:
      #result = subprocess.run(build_command, capture_output=True, text=True, )
      process = subprocess.Popen(build_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=f"{self.config['application']['applicationpath']}/{self.config['containerbuild']['containerdirectory']}")

      # Read and print output line by line
      self.run_code_with_alive_bar(process = process, text=f"Building container ({build_command[3]}) ...", debug = self.debug)

      process.stdout.close()
      process.wait()

      image_name = build_command[3]
      #print(result.stdout)
      #print(result.stderr)
      if process.returncode != 0:
        raise Exception("Something went wrong!")

      return image_name
    except FileNotFoundError:
      print("The specified directory does not exist.")
    except subprocess.CalledProcessError as e:
      print(f"Command failed: {e}")
    except Exception as e:
      print(f"Error building local container: {e}")

  def deploy_local(self):
    print("Starting local deploy..")

    #try:
    #  fishshellc = FishShell()
    #except Exception as e:
    #  print(f"Error creating Fish shell: {e}")
    #  return None

    try:
      #environment_variables = fishshellc.get_env_variables()
      environment_variables = dotenv_values(".env")
    except Exception as e:
      print(f"Error getting environment variables: {e}")

    # Base container
    try:
      build_command_base = self.deployeee.get_base_container_build_command(self.environment, environment_variables)
    except Exception as e:
      print(f"Error building base container build command: {e}")

    try:
      base_image_name = self.build_container(build_command_base)
    except Exception as e:
      print(f"Error building base container: {e}")

    # Container
    try:
      build_system_args = self.deployeee.get_container_build_command(self.environment)
    except Exception as e:
      print(f"Error building build command: {e}")

    try:
      image_name = self.build_container(build_system_args)
    except Exception as e:
      print(f"Error building container: {e}")

    # Pushing Image
    if not self.command_line_parameters.dont_upload:
      try:
        self.push_image(image_name)
      except Exception as e:
        print(f"Error pushing image: {e}")

    print(f"Finished.")



  def run_code_with_alive_bar(self, *args, **kwargs):
    if kwargs["debug"] == False:
      print(kwargs["text"])
    if alive_progress_package:
      with alive_bar(100) as bar:
        for _ in range(100):
          for line_stdout in iter(kwargs["process"].stdout.readline, ''):
            if kwargs["debug"] == True:
              print(line_stdout, end='')  # `end=''` prevents double newlines
          time.sleep(0.05)
          bar()
    else:
      if kwargs["debug"] == True:
        for line_stdout in iter(kwargs["process"].stdout.readline, ''):
          print(line_stdout, end='')  # `end=''` prevents double newlines

  def run_command_live(self, command):
    try:
      process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
      )

      for line in iter(process.stdout.readline, ''):
         sys.stdout.write(line)
         sys.stdout.flush()  # Forces immediate printing

      # Read and print output line by line
      #self.run_code_with_alive_bar(process = process, text = f"Running container ...", debug = True)

      #process.stdout.close()
      #process.wait()

    except KeyboardInterrupt:
      print("\nProcess interrupted. Terminating gracefully...")
      process.terminate()  # Send SIGTERM
      try:
        process.wait(timeout=5)  # Give it time to exit cleanly
      except subprocess.TimeoutExpired:
        process.kill()  # Force kill if it hangs

    finally:
      if process.poll() is None:  # Check if process is still running
        process.kill()
      process.stdout.close()
      print(f"Finished.")

  def run_local(self):
    try:
      run_engine = self.deployeee.get_config_value_by_section(self.config['containerrun'], key='runengine', environment=self.environment)
      if run_engine in self.config['runengines']['runengines']:
        run_engine_parameters = self.deployeee.get_json_from_config(self.config['runengines']['runengines'])[run_engine]
        '''Prepared'''
        port = self.deployeee.get_config_value_by_section(self.config['containerrun'], key='published_ports', environment=self.environment)
        #fernet_key = os.getenv('FERNET_KEY')
        #if fernet_key:
        #  env = f"FERNET_KEY={fernet_key}"
        #else:
        #  env = None
        # *( ["--env", env] if env is not None else [] ),

        try:
          run_command = [run_engine, "run", "--rm", "-p", f"{port}:{port}", f"--env-file", f".env", self.deployeee.get_image_name()]
        except Exception as e:
          print(f"Error building run command: {e}")

    except Exception as e:
      print("Error constructing run command", e)
      sys.exit(1)

    try:
      result = self.run_command_live(run_command)
      return result
    except Exception as e:
      print("Error running container locally", e)
      sys.exit(2)

    print(f"Finished.")

  def is_logged_in(self, registry: str) -> bool:
    auth_file = os.path.expanduser("~/.config/containers/auth.json")

    if not os.path.exists(auth_file):
      print("No auth.json file found.")
      return False

    with open(auth_file, "r") as f:
      data = json.load(f)

    auths = data.get("auths", {})

    if registry in auths:
      encoded = auths[registry].get("auth")
      if encoded:
        decoded = base64.b64decode(encoded).decode()
        username = decoded.split(":")[0]
        print(f"✅ Logged in to {registry} as {username}")
        return True

    print(f"❌ Not logged in to {registry}")
    return False

  def push_image(self, image_name):
    # Define image name and tag
    full_image_name = image_name
    username = self.config["deployment"]["docker_hub_username"]

    if self.config["containerbuild"]["buildsystem"] == "podman":
      # Tag
      try:
        subprocess.run(["podman", "tag", full_image_name, f"docker.io/{username}/{full_image_name}"], check=True)
        print("✅ Successfully tagged image")
      except subprocess.CalledProcessError as e:
        print(f"❌ Error tagging: {e}")

      # Step 2: Authenticate to Docker Hub
      if not self.is_logged_in("docker.io"):
        try:
          subprocess.run(["podman", "login", "--username", username, "docker.io"], check=True)
          print("✅ Successfully logged into Docker Hub")
        except subprocess.CalledProcessError as e:
          print(f"❌ Login failed: {e}")
          raise Exception("Error logging into docker.io.")

      # Step 3: Push the image to Docker Hub
      try:
        process = subprocess.Popen(["podman", "push", f"docker.io/{username}/{full_image_name}"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        # Read and print output line by line
        self.run_code_with_alive_bar(process = process, text=f"Pushing image ({full_image_name}) ...", debug = self.debug)
        process.stdout.close()
        process.wait()
        if process.returncode != 0:
          raise Exception("Error running push command.")
        print(f"✅ Successfully pushed image: {full_image_name} to Docker Hub")
      except subprocess.CalledProcessError as e:
        print(f"❌ Error pushing image: {e}")


  def deploy_cloud(self):
    print("Starting cloud deploy..")
    ci = CI(self.deployeee.config, self.deployeee, deploy=self)
    print(f"Finished.")

  def store_github(self):
    print("Storing GitHub secrets...")
    githubc = GitHub(self.deployeee, os.getenv('GITHUB_SECRETS'))
