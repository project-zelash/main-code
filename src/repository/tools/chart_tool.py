from src.repository.tools.base_tool import BaseTool

class ChartTool(BaseTool):
    """
    Tool for generating data visualizations.
    """
    
    def __init__(self, chart_script_path=None):
        """
        Constructor with path to chart generation script.
        
        Args:
            chart_script_path: Path to Node.js chart generation script.
        """
        name = "chart"
        description = "Generate data visualizations"
        args_schema = {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line", "pie", "scatter"],
                    "description": "Type of chart to generate"
                },
                "title": {
                    "type": "string",
                    "description": "Chart title text"
                },
                "data": {
                    "type": "object",
                    "description": "Dataset for visualization"
                },
                "x_label": {
                    "type": "string",
                    "description": "Label for X-axis"
                },
                "y_label": {
                    "type": "string",
                    "description": "Label for Y-axis"
                },
                "output_format": {
                    "type": "string",
                    "enum": ["png", "html"],
                    "description": "Output format for the chart"
                }
            },
            "required": ["chart_type", "data"]
        }
        
        super().__init__(name, description, args_schema)
        self.chart_script_path = chart_script_path or "./chart_generator.js"
    
    def run(self, chart_type, title=None, data=None, x_label=None, y_label=None, output_format="png"):
        """
        Generates visualization.
        
        Args:
            chart_type: Type of chart ("bar", "line", "pie", "scatter").
            title: Chart title text.
            data: Dataset for visualization.
            x_label, y_label: Axis labels.
            output_format: Output type ("png" or "html").
            
        Returns:
            Path to generated chart file or HTML content.
        """
        # Implementation will generate chart using Node.js script with VisActor library
        # and return result (file path or HTML content)
        pass