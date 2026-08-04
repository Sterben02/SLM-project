# examples/example_repo/utils.py
import subprocess

def run_command(user_input):
    # ОПАСНО: shell=True с пользовательским вводом
    subprocess.run(f"ls {user_input}", shell=True)

def calc(expression):
    # ОПАСНО: eval с пользовательским вводом
    return eval(expression)