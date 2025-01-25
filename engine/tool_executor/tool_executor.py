import os
import subprocess


def execute_tool(tool_name: str, method: str, kwargs: dict):
    python_executable = "./venv/bin/python"  # Unix/Linux/macOS
    # python_executable = r'C:\path\to\second_project\venv\Scripts\python.exe'  # Windows

    # Main script path of the second project
    script_path = f"./tools/{tool_name}/main.py"
    env = os.environ.copy()

    # Optional: parameters passed to the second project
    args = [method, kwargs]

    # Build command
    command = [python_executable, script_path, method] + args

    try:
        # Run command and capture output
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        print("Output from second project:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error running second project:")
        print(e.stderr)
