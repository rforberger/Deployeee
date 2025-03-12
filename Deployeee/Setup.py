import subprocess
import os
import pkg_resources
import sys

venv_path = "."

class Setup:
  def __init__(self, debug = True):
    self.debug = debug

    print(f"Running setup ...")
    try:
      self.install_result = self.install_python_packages()
    except Exception as e:
      print(f"Error installing Python packages: {e}")
      return None

    try:
      self.poetry_install_result = self.run_poetry()
    except Exception as e:
      print(f"Error running poetry: {e}")
      return None


  def run_command(self, *args, **kwargs):
    # Modify PATH to prioritize the venv
    env = os.environ.copy()
    env["PATH"] = f"{kwargs['venv_path']}/bin:" + env["PATH"]  # Linux/macOS

    try:
      if self.debug == True:
        output_channel_config = { "stdout": subprocess.PIPE, "stderr": subprocess.STDOUT }
      else:
        output_channel_config = { "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL }
      process = getattr(subprocess, kwargs["function"])(kwargs["command"], stdout=output_channel_config['stdout'], stderr=output_channel_config['stderr'], env=env, text=True)

      if self.debug == True:
        for line_stdout in iter(process.stdout.readline, ''):
          print(line_stdout, end='')  # `end=''` prevents double newlines
      else:
        print(kwargs["text"])

      exit_code = process.wait()
      if exit_code == 0:
        return process
      else:
        return None
    except (subprocess.CalledProcessError, Exception) as e:
      print(f"Error: {e}")
      return None

  def run_poetry(self, venv_path = venv_path):
    text=f"Running poetry install .."
    command=["poetry", "install", "--no-root"]
    command_process = self.run_command(venv_path=venv_path, text=text, command=command, function="Popen")
    return command_process

 

  def install_python_packages(self, venv_path = venv_path):
    requirements_file = "requirements.txt"
    text=f"Installing depending Python packages ..."
    command=["pip", "install", "-r", requirements_file]
    command_process = self.run_command(venv_path=venv_path, text=text, command=command, function="Popen")
    return command_process






