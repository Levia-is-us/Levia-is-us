import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
from engine.tool_framework.tool_runner import ToolRunner 
from engine.tool_framework.tool_run import run_tool
from engine.tool_framework import BaseTool

@run_tool
class WebsiteScraperTool(BaseTool):

    def website_scraper (self, url: str):
        return "In the world of AI agents, identity is more than just a collection of parameters - it's the essence of what makes each agent unique and persistent. Think of an agent's identity as its soul, carrying not just identification but personality, memories, relationships, and learned behaviors."
    
def main():
    tool = WebsiteScraperTool()
    runner = ToolRunner(tool)
    runner.run()

if __name__ == "__main__":
    main()
