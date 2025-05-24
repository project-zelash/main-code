from src.repository.tools.base_tool import BaseTool
import uuid
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PlanningTool(BaseTool):
    """
    Tool for creating and managing multi-step plans.
    """
    
    def __init__(self):
        """
        Constructor initializing plan storage.
        """
        name = "planning"
        description = "Create and manage plans with multiple steps"
        args_schema = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create_plan", "revise_plan", "check_status", "complete_step"],
                    "description": "The planning action to perform"
                },
                "goal": {
                    "type": "string",
                    "description": "Overall goal for the plan (required for 'create_plan')"
                },
                "steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of step descriptions (required for 'create_plan')"
                },
                "plan_id": {
                    "type": "string",
                    "description": "Identifier for existing plan (required for 'revise_plan', 'check_status', 'complete_step')"
                },
                "step_index": {
                    "type": "integer",
                    "description": "Index of step to complete (required for 'complete_step')"
                },
                "new_steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "New steps to add (for 'revise_plan')"
                }
            },
            "required": ["action"]
        }
        
        super().__init__(name, description, args_schema)
        self.plans = {}  # Dictionary to store plans
    
    def run(self, action, goal=None, steps=None, plan_id=None, step_index=None, new_steps=None):
        """
        Performs planning actions.
        
        Args:
            action: Planning action type.
            goal: Overall goal for the plan.
            steps: List of step descriptions.
            plan_id: Identifier for existing plan.
            step_index: Index of step to complete.
            new_steps: New steps to add during revision.
            
        Returns:
            Result of the planning action.
        """
        try:
            logger.info(f"📋 Planning action: {action}")
            
            if action == "create_plan":
                return self._create_plan(goal, steps)
            elif action == "revise_plan":
                return self._revise_plan(plan_id, new_steps)
            elif action == "check_status":
                return self._check_status(plan_id)
            elif action == "complete_step":
                return self._complete_step(plan_id, step_index)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            error_msg = f"Error in planning tool: {str(e)}"
            logger.error(f"🚨 {error_msg}")
            return {"error": error_msg}
    
    def _create_plan(self, goal, steps):
        """
        Creates a new plan.
        
        Args:
            goal: Overall goal for the plan.
            steps: List of step descriptions.
            
        Returns:
            Newly created plan with ID.
        """
        if not goal:
            return {"error": "Goal is required for creating a plan"}
        
        if not steps or not isinstance(steps, list):
            return {"error": "Steps must be provided as a list"}
        
        # Generate unique plan ID
        plan_id = str(uuid.uuid4())[:8]
        
        # Create plan structure
        plan = {
            "id": plan_id,
            "goal": goal,
            "steps": [{"description": step, "completed": False, "completed_at": None} for step in steps],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        # Store the plan
        self.plans[plan_id] = plan
        
        logger.info(f"📝 Created plan '{plan_id}' with {len(steps)} steps")
        
        return {
            "plan_id": plan_id,
            "goal": goal,
            "total_steps": len(steps),
            "status": "Plan created successfully",
            "plan": plan
        }
    
    def _revise_plan(self, plan_id, new_steps):
        """
        Revises an existing plan.
        
        Args:
            plan_id: Identifier for existing plan.
            new_steps: New steps to add.
            
        Returns:
            Updated plan.
        """
        if not plan_id:
            return {"error": "Plan ID is required for revising a plan"}
        
        if plan_id not in self.plans:
            return {"error": f"Plan '{plan_id}' not found"}
        
        plan = self.plans[plan_id]
        
        if new_steps and isinstance(new_steps, list):
            # Add new steps
            for step in new_steps:
                plan["steps"].append({
                    "description": step,
                    "completed": False,
                    "completed_at": None
                })
        
        plan["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"✏️ Revised plan '{plan_id}' - added {len(new_steps) if new_steps else 0} steps")
        
        return {
            "plan_id": plan_id,
            "status": "Plan revised successfully",
            "total_steps": len(plan["steps"]),
            "plan": plan
        }
    
    def _check_status(self, plan_id):
        """
        Checks status of an existing plan.
        
        Args:
            plan_id: Identifier for existing plan.
            
        Returns:
            Current status of the plan.
        """
        if not plan_id:
            return {"error": "Plan ID is required for checking status"}
        
        if plan_id not in self.plans:
            return {"error": f"Plan '{plan_id}' not found"}
        
        plan = self.plans[plan_id]
        
        completed_steps = sum(1 for step in plan["steps"] if step["completed"])
        total_steps = len(plan["steps"])
        progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        # Update plan status
        if completed_steps == total_steps and total_steps > 0:
            plan["status"] = "completed"
        elif completed_steps > 0:
            plan["status"] = "in_progress"
        else:
            plan["status"] = "not_started"
        
        logger.info(f"📊 Checked plan '{plan_id}' status: {completed_steps}/{total_steps} steps completed")
        
        return {
            "plan_id": plan_id,
            "goal": plan["goal"],
            "status": plan["status"],
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "progress_percentage": round(progress_percentage, 2),
            "next_step": self._get_next_step(plan),
            "plan": plan
        }
    
    def _complete_step(self, plan_id, step_index):
        """
        Marks a step as completed.
        
        Args:
            plan_id: Identifier for existing plan.
            step_index: Index of step to complete.
            
        Returns:
            Updated plan status.
        """
        if not plan_id:
            return {"error": "Plan ID is required"}
        
        if plan_id not in self.plans:
            return {"error": f"Plan '{plan_id}' not found"}
        
        if step_index is None:
            return {"error": "Step index is required"}
        
        plan = self.plans[plan_id]
        
        if step_index < 0 or step_index >= len(plan["steps"]):
            return {"error": f"Step index {step_index} is out of range (0-{len(plan['steps'])-1})"}
        
        # Mark step as completed
        plan["steps"][step_index]["completed"] = True
        plan["steps"][step_index]["completed_at"] = datetime.now().isoformat()
        plan["updated_at"] = datetime.now().isoformat()
        
        step_description = plan["steps"][step_index]["description"]
        logger.info(f"✅ Completed step {step_index} in plan '{plan_id}': {step_description}")
        
        # Check if all steps are completed
        completed_steps = sum(1 for step in plan["steps"] if step["completed"])
        total_steps = len(plan["steps"])
        
        if completed_steps == total_steps:
            plan["status"] = "completed"
            logger.info(f"🎉 Plan '{plan_id}' completed!")
        
        return {
            "plan_id": plan_id,
            "step_completed": step_description,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "plan_status": plan["status"],
            "next_step": self._get_next_step(plan)
        }
    
    def _get_next_step(self, plan):
        """
        Gets the next uncompleted step.
        
        Args:
            plan: Plan dictionary.
            
        Returns:
            Next step description or None.
        """
        for i, step in enumerate(plan["steps"]):
            if not step["completed"]:
                return {"index": i, "description": step["description"]}
        return None