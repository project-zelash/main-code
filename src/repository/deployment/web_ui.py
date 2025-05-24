import gradio as gr
import os
import json

from src.repository.agent.general_agent import GeneralAgent
from src.repository.llm.openai_llm import OpenAILLM
from src.repository.llm.anthropic_llm import AnthropicLLM
from src.repository.llm.bedrock_llm import BedrockLLM

class WebUI:
    """
    Graphical user interface built with Gradio.
    """
    
    def __init__(self):
        """
        Initialize the web UI.
        """
        self.agent = None
        self.memory = []
        self.available_tools = {}
        self.enabled_tools = {}
        
    def initialize_agent(self, llm_provider, model_name, temperature, agent_type, enabled_tools_list):
        """
        Initialize the agent with specified configuration.
        
        Args:
            llm_provider: LLM provider name (openai, anthropic, bedrock).
            model_name: Model name to use.
            temperature: Temperature value for generation.
            agent_type: Type of agent to create.
            enabled_tools_list: List of tool names to enable.
            
        Returns:
            Success message or error.
        """
        try:
            # Create LLM
            llm = self._create_llm(llm_provider, model_name, temperature)
            
            # Filter tools
            tools = {name: tool for name, tool in self.available_tools.items() 
                    if name in enabled_tools_list}
            
            # Create agent
            if agent_type == "manus":
                self.agent = ManusAgent(llm, tools, name="ManusAgent", verbose=True)
            elif agent_type == "research":
                from src.repository.agent.research_agent import ResearchAgent
                self.agent = ResearchAgent(llm, tools, verbose=True)
            elif agent_type == "analysis":
                from src.repository.agent.analysis_agent import AnalysisAgent
                self.agent = AnalysisAgent(llm, tools, verbose=True)
            elif agent_type == "writing":
                from src.repository.agent.writing_agent import WritingAgent
                self.agent = WritingAgent(llm, tools, verbose=True)
            else:
                return f"Unknown agent type: {agent_type}"
                
            self.enabled_tools = tools
            return f"Agent initialized with {len(tools)} tools"
        except Exception as e:
            return f"Error initializing agent: {str(e)}"
    
    def _create_llm(self, provider, model_name, temperature):
        """
        Create LLM instance.
        
        Args:
            provider: LLM provider name.
            model_name: Model name.
            temperature: Temperature value.
            
        Returns:
            LLM instance.
        """
        if provider == "openai":
            return OpenAILLM(model=model_name, temperature=temperature)
        elif provider == "anthropic":
            return AnthropicLLM(model=model_name, temperature=temperature)
        elif provider == "bedrock":
            return BedrockLLM(model=model_name, temperature=temperature)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    def chat(self, message, history):
        """
        Process a chat message.
        
        Args:
            message: User's message.
            history: Chat history from Gradio.
            
        Returns:
            Updated history.
        """
        if not self.agent:
            return history + [[message, "Agent not initialized. Please configure and initialize the agent first."]]
            
        try:
            response = self.agent.run(message)
            return history + [[message, response]]
        except Exception as e:
            return history + [[message, f"Error: {str(e)}"]]
    
    def launch_ui(self, share=False):
        """
        Launch the Gradio web interface.
        
        Args:
            share: Whether to create a public link.
            
        Returns:
            Gradio Blocks instance.
        """
        # Create UI components
        with gr.Blocks(title="Zelash AI Framework") as demo:
            gr.Markdown("# Zelash AI Framework")
            
            with gr.Tab("Chat"):
                chatbot = gr.Chatbot()
                msg = gr.Textbox()
                clear = gr.Button("Clear")
                
                msg.submit(self.chat, [msg, chatbot], [chatbot])
                clear.click(lambda: None, None, chatbot, queue=False)
                
            with gr.Tab("Settings"):
                with gr.Row():
                    with gr.Column():
                        llm_provider = gr.Dropdown(
                            ["openai", "anthropic", "bedrock"], 
                            label="LLM Provider", 
                            value="openai"
                        )
                        model_name = gr.Textbox(label="Model Name", value="gpt-4o")
                        temperature = gr.Slider(0.0, 1.0, 0.7, label="Temperature")
                        
                    with gr.Column():
                        agent_type = gr.Dropdown(
                            ["manus", "research", "analysis", "writing"], 
                            label="Agent Type", 
                            value="manus"
                        )
                        tool_checkboxes = gr.CheckboxGroup(
                            list(self.available_tools.keys()),
                            label="Enabled Tools",
                            value=list(self.available_tools.keys())
                        )
                
                init_button = gr.Button("Initialize Agent")
                init_result = gr.Textbox(label="Initialization Result")
                
                init_button.click(
                    self.initialize_agent,
                    [llm_provider, model_name, temperature, agent_type, tool_checkboxes],
                    init_result
                )
        
        # Launch the interface
        demo.launch(share=share)
        return demo
        
    def load_tools(self, tools_dict):
        """
        Load tools from a dictionary.
        
        Args:
            tools_dict: Dictionary of tool instances.
        """
        self.available_tools = tools_dict