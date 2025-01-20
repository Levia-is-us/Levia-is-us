from typing import Any, Optional, Dict, List
from tool_framewotk.tool_registry import ToolRegistry
from tool_framewotk import BaseTool
import subprocess
import json
import sys
import os

class ToolCaller:
    """Class for calling tools"""
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def call_tool(self, tool_name: str, method: str, **kwargs) -> Optional[Dict]:
        """Call a specific tool method"""
        tool_path = self.registry.get_tool_path(tool_name)
        if not tool_path:
            raise ValueError(f"Tool '{tool_name}' not found")

        try:
            # Start tool process
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.dirname(os.path.dirname(tool_path))
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'  # Disable debugger warnings
            
            process = subprocess.Popen(
                [sys.executable, tool_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )

            # Prepare input data
            input_data = {
                "method": method,
                "args": kwargs
            }

            # Send input and get output
            print(f"Sending input to tool: {input_data}")
            stdout, stderr = process.communicate(json.dumps(input_data, ensure_ascii=False) + '\n')

            # Filter out debugger warnings
            real_stderr = '\n'.join(line for line in stderr.splitlines() 
                                  if 'Debugger warning' not in line 
                                  and 'PYDEVD' not in line
                                  and line.strip())

            if real_stderr:
                print(f"Tool stderr: {real_stderr}", file=sys.stderr)

            if stdout:
                try:
                    result = json.loads(stdout)
                    print(f"Tool returned: {result}")
                    return result.get('result') if isinstance(result, dict) and 'result' in result else result
                except json.JSONDecodeError as e:
                    print(f"Failed to parse tool output: {stdout}", file=sys.stderr)
                    return None

            print("Tool returned no output")
            return None

        except Exception as e:
            print(f"Error calling tool: {str(e)}", file=sys.stderr)
            return None

