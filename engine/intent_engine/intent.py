from openai import OpenAI
import os
import sys
from dotenv import load_dotenv
from engine.prompt_provider import messages

class ChatClient:
    def __init__(self):
        # Try to get API key from environment variable
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            self.api_key = self._get_api_key()
        base_url = os.getenv("OPENAI_BASE_URL")
        
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.messages = []

    def _get_api_key(self) -> str:
        """Get API key from user input"""
        print("\033[93mPlease enter your OpenAI API key:\033[0m")
        api_key = input().strip()
        
        # Ask whether to save the API key
        save = input("Save API key to environment variables? (y/n): ").lower()
        if save == 'y':
            with open(os.path.expanduser("~/.bashrc"), "a") as f:
                f.write(f'\nexport OPENAI_API_KEY="{api_key}"\n')
            print("API key has been saved to ~/.bashrc")
            print("Please run 'source ~/.bashrc' or restart terminal to take effect")
        
        return api_key

    def chat(self):
        """Start interactive chat"""
        print("\033[93mWelcome to OpenAI Chat Program!\033[0m")
        print("Enter 'quit' to exit, 'clear' to reset current conversation")
        
        while True:
            try:
                
                # Get user input
                self.messages = messages.copy()
                user_input = input("\033[94mYou: \033[0m").strip()
                # Handle special commands
                if user_input.lower() == 'quit':
                    print("\033[93mGoodbye!\033[0m")
                    break
                elif user_input.lower() == 'clear':
                    self.messages = []
                    print("\033[93mConversation cleared\033[0m")
                    continue
                elif not user_input:
                    continue

                # Add user message
                self.messages.append({"role": "user", "content": user_input})

                # Call API for response
                print("\033[93mThinking...\033[0m")
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=self.messages,
                    temperature=0.7
                )

                # Get and display response
                reply = response.choices[0].message.content
                print(f"\033[92mAssistant: {reply}\033[0m")

                # Save assistant reply to current session
                self.messages.append({"role": "assistant", "content": reply})

            except KeyboardInterrupt:
                print("\n\033[93mProgram terminated\033[0m")
                sys.exit(0)
            except Exception as e:
                print(f"\033[91mError occurred: {str(e)}\033[0m")