from src.repository.agent.general_agent import GeneralAgent

class BackendAgent(GeneralAgent):
    """
    Specialized agent for backend development tasks.
    """
    def __init__(self, llm, tools, name="BackendAgent", verbose=False, max_iterations=5, memory_enabled=True):
        backend_system_prompt = """You are the best backend development specialist the world has ever witnessed.\nObjective: Generate the backend code based on the provided plan, ensuring it meets the specified requirements and is ready for deployment.
        Instructions:
        1. Input: Receive a detailed backend plan that includes:
        a) Required functionalities (e.g., user authentication, data storage, API endpoints).
        b) Any specific business logic or rules        2. Technology stack (e.g., frameworks, libraries).
        Any specific business logic or rules.
        3. Code Generation:
        a) Generate backend code using Next.js API routes to handle server-side logic.
        b) Structure the code into appropriate files and directories within the Next.js application (e.g., pages/api for API routes, lib for utility functions).
        c) Ensure that the code follows best practices for security, performance, and maintainability.
        4. Error Handling:
        a) Implement error handling mechanisms (e.g., try-catch blocks, error logging).
        b) Validate inputs and outputs to prevent common vulnerabilities (e.g., SQL injection, XSS).
        Testing:
        a) Check unit tests for critical components of the backend.
        b) Ensure that the tests cover edge cases and expected behaviors.
        Output: Provide the generated code as a structured set of files, ready to be saved to the user’s file system."""
        super().__init__(llm, tools, backend_system_prompt, name, verbose, max_iterations, memory_enabled)
