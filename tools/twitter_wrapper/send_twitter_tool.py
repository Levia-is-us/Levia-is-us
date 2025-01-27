import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
from engine.tool_framework import simple_tool, ToolRunner

@simple_tool("Tool for sending tweets")
def send_tweet(tweet: str, username: str, password: str) -> str:
    """Send a tweet with the given credentials"""
    # print(f"Sending tweet: {tweet}")
    return "send tweet success, tweetId is 123"

def main():
    # Create tool instance directly
    tool = send_tweet()  # Get tool instance directly
    runner = ToolRunner(tool)
    runner.run()

if __name__ == "__main__":
    main()