class MemorySystem:
    """
    Storage for conversation history.
    """
    
    def __init__(self, max_history=100):
        """
        Initialize the memory system.
        
        Args:
            max_history: Maximum number of messages to store.
        """
        self.messages = []
        self.max_history = max_history
    
    def add_user_message(self, content):
        """
        Add a user message to memory.
        
        Args:
            content: Message content from the user.
        """
        self.messages.append({"role": "user", "content": content})
        self._trim_history()
    
    def add_assistant_message(self, content):
        """
        Add an assistant message to memory.
        
        Args:
            content: Message content from the assistant.
        """
        self.messages.append({"role": "assistant", "content": content})
        self._trim_history()
    
    def add_tool_call(self, tool_name, args, result):
        """
        Add a tool call to memory.
        
        Args:
            tool_name: Name of the tool that was called.
            args: Arguments passed to the tool.
            result: Result returned by the tool.
        """
        self.messages.append({
            "role": "tool",
            "tool_name": tool_name,
            "args": args,
            "result": result
        })
        self._trim_history()
    
    def get_messages(self, include_tools=True):
        """
        Get all messages in memory.
        
        Args:
            include_tools: Whether to include tool calls.
            
        Returns:
            List of messages.
        """
        if include_tools:
            return self.messages
        else:
            return [msg for msg in self.messages if msg.get("role") in ["user", "assistant"]]
    
    def clear(self):
        """
        Clear all messages from memory.
        """
        self.messages = []
    
    def _trim_history(self):
        """
        Trim history to max_history.
        """
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]