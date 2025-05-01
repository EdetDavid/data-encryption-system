# Ensure the migrations folder has an __init__.py file to make it a valid Python package
import os

def ensure_init_py(migrations_folder):
    init_file = os.path.join(migrations_folder, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# This file makes the migrations folder a Python package\n')