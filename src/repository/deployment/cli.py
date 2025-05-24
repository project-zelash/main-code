import argparse
import sys
import os

from src.repository.agent.general_agent import GeneralAgent
from src.repository.llm.openai_llm import OpenAILLM
from src.repository.llm.anthropic_llm import AnthropicLLM
from src.repository.llm.bedrock_llm import BedrockLLM

class CLI:
    """
    Command-line interface for running agents.
    """
    
    def __init__(self):
        """
        Initialize the CLI.
        """
        self.parser = self._create_parser()
        self.agent = None
    
    def _create_parser(self):
        """
        Create argument parser.
        
        Returns:
            Configured ArgumentParser.
        """
        parser = argparse.ArgumentParser(description="Zelash CLI - AI Agent Framework")
        
        # Mode selection
        parser.add_argument("--mode", choices=["single", "flow", "mcp"], default="single",
                            help="Mode of operation: single agent, agent flow, or MCP")
        
        # LLM configuration
        parser.add_argument("--llm", choices=["openai", "anthropic", "bedrock"], default="openai",
                            help="LLM provider to use")
        parser.add_argument("--model", type=str, help="Model name to use (specific to LLM provider)")
        parser.add_argument("--temperature", type=float, default=0.7, help="Temperature for LLM generation")
        
        # Agent configuration
        parser.add_argument("--agent", choices=["manus", "research", "analysis", "writing"], default="manus",
                            help="Type of agent to use (in single mode)")
        parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
        
        # Tool configuration
        parser.add_argument("--disable-tools", type=str, nargs="*", help="List of tools to disable")
        
        # Flow configuration
        parser.add_argument("--flow-config", type=str, help="Path to flow configuration file (in flow mode)")
        
        # MCP configuration
        parser.add_argument("--mcp-server", action="store_true", help="Run as MCP server")
        parser.add_argument("--mcp-url", type=str, default="ws://localhost:8765", 
                            help="URL of MCP server (for client mode)")
        
        return parser
    
    def run(self, args=None):
        """
        Run the CLI.
        
        Args:
            args: Command-line arguments (if None, sys.argv is used).
            
        Returns:
            Exit code.
        """
        args = self.parser.parse_args(args)
        
        # Set up LLM
        llm = self._create_llm(args)
        if not llm:
            return 1
            
        # Create agent based on mode
        if args.mode == "single":
            self._run_single_mode(args, llm)
        elif args.mode == "flow":
            self._run_flow_mode(args, llm)
        elif args.mode == "mcp":
            self._run_mcp_mode(args, llm)
        
        return 0
    
    def _create_llm(self, args):
        """
        Create LLM instance based on args.
        
        Args:
            args: Parsed arguments.
            
        Returns:
            LLM instance.
        """
        # Implementation will create appropriate LLM instance based on args
        pass
    
    def _run_single_mode(self, args, llm):
        """
        Run in single agent mode.
        
        Args:
            args: Parsed arguments.
            llm: LLM instance.
        """
        # Implementation will create and run a single agent
        pass
    
    def _run_flow_mode(self, args, llm):
        """
        Run in agent flow mode.
        
        Args:
            args: Parsed arguments.
            llm: LLM instance.
        """
        # Implementation will create and run an agent flow
        pass
    
    def _run_mcp_mode(self, args, llm):
        """
        Run in MCP mode.
        
        Args:
            args: Parsed arguments.
            llm: LLM instance.
        """
        # Implementation will run MCP server or client
        pass
    
    def _interactive_loop(self):
        """
        Run interactive input loop.
        """
        print("Zelash CLI - Enter 'exit' to quit")
        while True:
            try:
                user_input = input("> ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                    
                if self.agent:
                    response = self.agent.run(user_input)
                    print(response)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    cli = CLI()
    sys.exit(cli.run())