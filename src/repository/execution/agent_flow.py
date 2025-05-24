import heapq
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import logging
import asyncio
from src.repository.mcp.mcp_client import MCPClient
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_mcp_context_sync(mcp_client, agent_name, task_input):
    """
    Synchronously fetch MCP context for the agent/task using MCPClient.
    """
    async def fetch():
        # You may want to customize the arguments for your context tool
        return await mcp_client.call_tool("get_context", agent=agent_name, input=task_input)
    return asyncio.run(fetch())

def run_agent_task(agent_name, agent_input, agents, mcp_client=None):
    agent_instance = agents.get(agent_name)
    if not agent_instance:
        raise ValueError(f"Agent {agent_name} not found")
    
    # Fetch MCP context if mcp_client is provided
    mcp_context = None
    if mcp_client is not None:
        try:
            mcp_context = fetch_mcp_context_sync(mcp_client, agent_name, agent_input)
        except Exception as e:
            # Log MCP connection failure but don't fail the task
            logger.warning(f"Failed to fetch MCP context for {agent_name}: {e}")
            mcp_context = None
    
    # If the agent has memory, pass its conversation_history as context
    if hasattr(agent_instance, 'memory_enabled') and getattr(agent_instance, 'memory_enabled', False):
        context = getattr(agent_instance, 'conversation_history', None)
        # Merge MCP context with conversation history
        merged_context = {"memory": context, "mcp": mcp_context}
        return agent_instance.run(agent_input, context=merged_context)
    return agent_instance.run(agent_input)

class AgentFlow:
    """
    Manages flow of information between multiple specialized agents using priority queue and subprocesses.
    """
    def __init__(self, agents, task_list, verbose=False, max_workers=4, mcp_server_url="ws://localhost:8765"):
        """
        Args:
            agents: Dictionary mapping agent names to instances.
            task_list: List of dicts, each with keys: 'name', 'agent', 'input', 'priority', 'dependencies' (list of task names)
            verbose: Boolean for detailed logging.
            max_workers: Number of parallel workers.
        """
        self.agents = agents
        self.task_list = task_list
        self.verbose = verbose
        self.max_workers = max_workers
        self.history = {
            'task': None,
            'agent': None,
            'input': None,
            'output': None
        }
        # Try to initialize MCP client, but don't fail if it's not available
        try:
            self.mcp_client = MCPClient(server_url=mcp_server_url)
        except Exception as e:
            logger.warning(f"Failed to initialize MCP client: {e}")
            self.mcp_client = None

    def run(self, max_retries=1):
        # Build dependency graph
        dependencies = {task['name']: set(task.get('dependencies', [])) for task in self.task_list}
        dependents = defaultdict(set)
        for task in self.task_list:
            for dep in task.get('dependencies', []):
                dependents[dep].add(task['name'])
        # Priority queue: (priority, task_name)
        ready_queue = []
        task_map = {task['name']: task for task in self.task_list}
        results = {}
        retries = defaultdict(int)
        # Initialize queue with tasks that have no dependencies
        for task in self.task_list:
            if not dependencies[task['name']]:
                heapq.heappush(ready_queue, (task.get('priority', 0), task['name']))
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            while ready_queue or futures:
                # Submit all ready tasks
                while ready_queue:
                    _, task_name = heapq.heappop(ready_queue)
                    task = task_map[task_name]
                    agent_name = task['agent']
                    agent_input = task['input']
                    if self.verbose:
                        logger.info(f"Submitting task {task_name} to agent {agent_name}")
                    try:
                        futures[executor.submit(run_agent_task, agent_name, agent_input, self.agents, self.mcp_client)] = task_name
                    except Exception as submit_exc:
                        logger.error(f"Failed to submit task {task_name} to agent {agent_name}: {submit_exc}")
                        results[task_name] = {
                            'error_type': type(submit_exc).__name__,
                            'error_message': str(submit_exc),
                            'traceback': traceback.format_exc(),
                            'stage': 'submit',
                            'agent': agent_name,
                            'task': task_name
                        }
                        continue
                # Wait for any task to complete
                for future in as_completed(list(futures)):
                    task_name = futures.pop(future)
                    try:
                        result = future.result()
                        results[task_name] = result
                        self.history['task'] = task_name
                        self.history['agent'] = task_map[task_name]['agent']
                        self.history['input'] = task_map[task_name]['input']
                        self.history['output'] = result
                        if self.verbose:
                            logger.info(f"Task {task_name} completed.")
                    except Exception as e:
                        retries[task_name] += 1
                        logger.error(f"Task {task_name} failed: {e}")
                        logger.error(traceback.format_exc())
                        results[task_name] = {
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'traceback': traceback.format_exc(),
                            'stage': 'execution',
                            'agent': task_map[task_name]['agent'],
                            'task': task_name
                        }
                        if retries[task_name] <= max_retries:
                            logger.warning(f"Retrying task {task_name} (attempt {retries[task_name]})")
                            heapq.heappush(ready_queue, (task_map[task_name].get('priority', 0), task_name))
                        else:
                            results[task_name] = {
                                'error_type': 'MaxRetriesExceeded',
                                'error_message': f"Task {task_name} failed after {max_retries} retries.",
                                'traceback': '',
                                'stage': 'max_retries',
                                'agent': task_map[task_name]['agent'],
                                'task': task_name
                            }
                            logger.error(f"Task {task_name} failed after {max_retries} retries.")
                    # Update dependents
                    for dep in dependents[task_name]:
                        if task_name in dependencies[dep]:
                            dependencies[dep].remove(task_name)
                        if not dependencies[dep]:
                            heapq.heappush(ready_queue, (task_map[dep].get('priority', 0), dep))
                    break  # Only process one completed future at a time
        return results

    def summarize_results(self, results=None):
        """
        Generate a user-facing summary of the agent flow results.
        Args:
            results: Optional results dict from run(). If None, uses last run.
        Returns:
            String summary for the user.
        """
        if results is None:
            results = {self.history['task']: self.history['output']} if self.history['task'] else {}
        summary = ["AgentFlow Execution Summary:"]
        if self.history['task']:
            summary.append(f"- Task '{self.history['task']}' (Agent: {self.history['agent']}):")
            output = self.history['output']
            if output is None:
                summary.append("    ❌ Failed or no result.")
            elif isinstance(output, str):
                summary.append(f"    Result: {output[:200]}{'...' if len(output) > 200 else ''}")
            else:
                summary.append(f"    Result: {str(output)[:200]}{'...' if len(str(output)) > 200 else ''}")
        else:
            summary.append("No tasks were executed.")
        return "\n".join(summary)