from src.repository.agent.general_agent import GeneralAgent
from src.repository.agent.research_agent import ResearchAgent
from src.repository.agent.analysis_agent import AnalysisAgent
from src.repository.agent.writing_agent import WritingAgent
from src.repository.agent.tool_call_agent import ToolCallAgent as ManusAgent
from src.repository.tools.base_tool import BaseTool
from src.repository.llm.base_language_model import BaseLanguageModel

class AgentService:
    """
    Service layer class for agent management and integration.
    """
    
    def __init__(self, llm_factory, tool_service):
        """
        Initialize the agent service.
        
        Args:
            llm_factory: Factory for creating LLM instances.
            tool_service: Service for accessing and managing tools.
        """
        self.llm_factory = llm_factory
        self.tool_service = tool_service
        self.agents = {}
    
    def create_agent(self, agent_type, agent_config):
        """
        Create an agent instance.
        
        Args:
            agent_type: Type of agent to create.
            agent_config: Configuration for the agent.
            
        Returns:
            Agent instance.
        """
        # Get LLM
        llm_config = agent_config.get("llm", {})
        llm = self.llm_factory.create_llm(
            provider=llm_config.get("provider", "openai"),
            model=llm_config.get("model"),
            temperature=llm_config.get("temperature", 0.7)
        )
        
        # Get tools
        tool_names = agent_config.get("tools", [])
        tools = self.tool_service.get_tools(tool_names)
        
        # Create agent based on type
        agent = None
        if agent_type == "manus":
            agent = ManusAgent(
                llm=llm,
                tools=tools,
                system_prompt=agent_config.get("system_prompt"),
                name=agent_config.get("name", "ManusAgent"),
                verbose=agent_config.get("verbose", False),
                max_iterations=agent_config.get("max_iterations", 5)
            )
        elif agent_type == "research":
            agent = ResearchAgent(
                llm=llm,
                tools=tools,
                name=agent_config.get("name", "ResearchAgent"),
                verbose=agent_config.get("verbose", False),
                max_iterations=agent_config.get("max_iterations", 5)
            )
        elif agent_type == "analysis":
            agent = AnalysisAgent(
                llm=llm,
                tools=tools,
                name=agent_config.get("name", "AnalysisAgent"),
                verbose=agent_config.get("verbose", False),
                max_iterations=agent_config.get("max_iterations", 5)
            )
        elif agent_type == "writing":
            agent = WritingAgent(
                llm=llm,
                tools=tools,
                name=agent_config.get("name", "WritingAgent"),
                verbose=agent_config.get("verbose", False),
                max_iterations=agent_config.get("max_iterations", 5)
            )
        elif agent_type == "general":
            agent = GeneralAgent(
                llm=llm,
                tools=tools,
                name=agent_config.get("name", "GeneralAgent"),
                verbose=agent_config.get("verbose", False),
                max_iterations=agent_config.get("max_iterations", 5)
            )
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Store agent if ID is provided
        agent_id = agent_config.get("id")
        if agent_id:
            self.agents[agent_id] = agent
            
        return agent
    
    def get_agent(self, agent_id):
        """
        Get an agent by ID.
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            Agent instance or None if not found.
        """
        return self.agents.get(agent_id)
    
    def run_query(self, agent_id, query):
        """
        Run a query with a specific agent.
        
        Args:
            agent_id: ID of the agent to use.
            query: Query to run.
            
        Returns:
            Result from the agent.
        """
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
            
        return agent.run(query)
    
    def delete_agent(self, agent_id):
        """
        Delete an agent.
        
        Args:
            agent_id: ID of the agent to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False