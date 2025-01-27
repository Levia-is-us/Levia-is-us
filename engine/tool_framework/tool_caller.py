from typing import Any, Optional, Dict, List
from .tool_registry import ToolRegistry
from .base_tool import BaseTool
import subprocess
import json
import sys
import os

class ToolCaller:
    """Class for calling tools"""
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def call_tool(self, tool_name: str, method: str, kwargs: Dict) -> Optional[Dict]:
        """Call a specific tool method"""
        tool_path = self.registry.get_tool_path(tool_name)
        if not tool_path:
            raise ValueError(f"Tool '{tool_name}' not found")

        try:
            # Start tool process
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.dirname(os.path.dirname(tool_path))
            env['PYTHONIOENCODING'] = 'utf-8'
            
            process = subprocess.Popen(
                [sys.executable, tool_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                text=True,
                bufsize=1,
                env=env
            )

            # Prepare input data
            input_data = {
                "method": method,
                "args": kwargs
            }

            # Send input and get output with timeout
            try:
                stdout, stderr = process.communicate(
                    json.dumps(input_data, ensure_ascii=False) + '\n',
                    timeout=30  # Add timeout
                )
                
                if stderr:
                    print(f"Tool stderr: {stderr}", file=sys.stderr)

                if stdout:
                    try:
                        result = json.loads(stdout.strip())
                        return result.get('result') if isinstance(result, dict) and 'result' in result else result
                    except json.JSONDecodeError:
                        print(f"Failed to parse tool output: {stdout!r}", file=sys.stderr)
                        return None

            except subprocess.TimeoutExpired:
                process.kill()
                print("Tool execution timed out", file=sys.stderr)
                return None

        except Exception as e:
            print(f"Error calling tool: {str(e)}", file=sys.stderr)
            return None

