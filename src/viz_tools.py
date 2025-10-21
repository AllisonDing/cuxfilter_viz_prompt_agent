# src/viz_tools.py - Dashboard tools handler
from typing import Dict, Any
from src.viz_code_generator import VizCodeGenerator
from src.viz_code_executor import VizCodeExecutor
from src.tools.viz_exp_store import VizExperimentStore

class VizTools:
    """Handler for dashboard creation tools."""
    
    def __init__(self, store: VizExperimentStore):
        self.store = store
        self.code_gen = VizCodeGenerator()
        self.code_execute = VizCodeExecutor()
        self.global_state = {}  # Persistent state across tool calls
    
    def get_tool_definitions(self):
        """Return tool definitions for the LLM."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "load_data",
                    "description": "Load dataset and prepare for dashboard creation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string", 
                                "description": "Path to data file (CSV, Arrow, Parquet)"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "describe_data",
                    "description": "Analyze dataset and recommend dashboard components",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_dashboard",
                    "description": "Create comprehensive cuxfilter dashboard with multiple charts, layout, and theme",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "config": {
                                "type": "string",
                                "description": "Dashboard configuration including chart types, columns, layout, theme, and widgets"
                            },
                            "num_charts": {
                                "type": "integer",
                                "description": "Number of charts to create",
                                "default": 3
                            },
                            "num_widgets": {
                                "type": "integer", 
                                "description": "Number of sidebar widgets",
                                "default": 2
                            },
                            "layout": {
                                "type": "string",
                                "description": "Layout name (feature_and_base, two_by_two, three_by_three, etc.)",
                                "default": "feature_and_base"
                            },
                            "theme": {
                                "type": "string",
                                "description": "Theme name (default, dark, rapids, rapids_dark)",
                                "default": "rapids_dark"
                            }
                        },
                        "required": ["config"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_charts",
                    "description": "Add more charts to existing dashboard",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "chart_configs": {
                                "type": "string",
                                "description": "Configuration for new charts to add"
                            }
                        },
                        "required": ["chart_configs"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "customize_dashboard",
                    "description": "Customize existing dashboard (change layout, theme, or chart properties)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "updates": {
                                "type": "string",
                                "description": "Description of customizations to apply"
                            }
                        },
                        "required": ["updates"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "show_dashboard",
                    "description": "Launch the interactive dashboard",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "export_dashboard",
                    "description": "Export dashboard to file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Path to save dashboard",
                                "default": "dashboard_export.html"
                            }
                        }
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a dashboard tool."""
        
        # Get current state description
        state_info = self.code_gen.get_state_description(self.global_state)
        
        # Generate code for the task
        code = self.code_gen.generate_code(tool_name, state_info, **kwargs)
        
        # Execute the generated code
        result = self.code_execute.execute_code(code, self.global_state)
        
        # Update global state with new variables
        if result['success']:
            self.global_state.update(result['globals'])
        
        # Prepare experiment data
        experiment_data = {
            'task': tool_name,
            'parameters': kwargs,
            'code': code,
            'success': result['success'],
            'results': result['results'],
            'error': result.get('error')
        }
        
        # Save experiment
        self.store.save_experiment(experiment_data)

        # Format response for user
        if result['success']:
            output_parts = [f"✓ {tool_name} completed successfully\n"]
        
            # Add dashboard file location if available
            if result.get("dashboard_file"):
                output_parts.append(f"📊 Dashboard saved to: {result['dashboard_file']}\n")
            
            if result.get("dashboard"):
                output_parts.append(f"\ndashboard: {result['dashboard']}")
            
            if result.get("charts"):
                output_parts.append(f"\ncharts: {result['charts']}")
            
            if result.get("widgets"):
                output_parts.append(f"\nwidgets: {result['widgets']}")
            
            if result.get("output"):
                output_parts.append(f"\n\nOutput:\n{result['output']}")
            
            return "".join(output_parts)
        else:
            return f"✗ {tool_name} failed: {result['error']}\n\nTraceback:\n{result.get('traceback', '')}"