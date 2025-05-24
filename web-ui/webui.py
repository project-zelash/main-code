import os
from dotenv import load_dotenv

# Always load .env from project root directory
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path)

def _print_google_api_key_debug():
    key = os.getenv("GOOGLE_API_KEY")
    if key:
        print(f"[DEBUG] GOOGLE_API_KEY loaded: ******{key[-4:]}")
    else:
        print("[DEBUG] GOOGLE_API_KEY not found in environment!")

_print_google_api_key_debug()
import argparse
from src.webui.interface import theme_map, create_ui


def main():
    parser = argparse.ArgumentParser(description="Gradio WebUI for Browser Agent")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address to bind to")
    parser.add_argument("--port", type=int, default=7788, help="Port to listen on")
    parser.add_argument("--theme", type=str, default="Ocean", choices=theme_map.keys(), help="Theme to use for the UI")
    args = parser.parse_args()

    demo = create_ui(theme_name=args.theme)
    demo.queue().launch(server_name=args.ip, server_port=args.port)


if __name__ == '__main__':
    main()
