import sys
import os
import json
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from engine.tool_framework import simple_tool, ToolRunner
import requests

@simple_tool("Get current location information")
def get_current_location(ip_address: str = None) -> dict:
    """Get location information for an IP address or current IP if not specified"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        if ip_address:
            url = f'https://ipapi.co/{ip_address}/json/'
        else:
            url = 'https://ipapi.co/json/'
            
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'ip': data.get('ip'),
                'city': data.get('city'),
                'region': data.get('region'),
                'country': data.get('country_name'),
                'location': f"{data.get('latitude')}, {data.get('longitude')}"
            }
        else:
            return {"error": f"API request failed with status code: {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"error": "Request timed out"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}

def main():
    # Create tool instance directly
    tool = get_current_location()  # Get tool instance directly
    runner = ToolRunner(tool)
    runner.run()

if __name__ == "__main__":
    main()