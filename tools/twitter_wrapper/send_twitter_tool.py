import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
from engine.tool_framework.tool_runner import ToolRunner 
from engine.tool_framework.tool_run import run_tool
from engine.tool_framework import BaseTool

@run_tool
class TwitterTool(BaseTool):

    def send_tweet(self, tweet: str):
        # print(f"Sending tweet: {tweet}")
        return "send tweet success, tweetId is 123"
    
def main():
    tool = TwitterTool()
    runner = ToolRunner(tool)
    runner.run()

if __name__ == "__main__":
    main()
