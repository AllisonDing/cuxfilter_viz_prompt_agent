# src/viz_tools.py - Pure orchestration, no hardcoded logic
from typing import Dict, Any
from src.viz_code_generator import VizCodeGenerator
from src.viz_code_executor import VizCodeExecutor
from src.tools.viz_exp_store import VizExperimentStore

class VizTools:
    """Pure orchestrator - generates code, executes it, stores results."""
    
    def __init__(self, store: VizExperimentStore):
        self.store = store
        self.code_gen = VizCodeGenerator()
        self.code_execute = VizCodeExecutor()
        self.global_state = {}  # Persistent state across tool calls
    
    def get_tool_definitions(self):
        """Return tool definitions for the LLM (pure API specs)."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "load_data",
                    "description": "Load dataset from file path and prepare for visualization. Converts to cudf GPU DataFrame and creates cuxfilter.DataFrame object.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string", 
                                "description": "File path (CSV, Arrow, or Parquet format)"
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
                    "description": "Analyze dataset structure and recommend appropriate visualizations based on column types and data characteristics.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_dashboard",
                    "description": "Create interactive GPU-accelerated dashboard with multiple charts, widgets, layout, and theme using cuxfilter.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "config": {
                                "type": "string",
                                "description": "Natural language description of desired dashboard: chart types, columns to visualize, layout preference, theme, and widgets needed"
                            },
                            "num_charts": {
                                "type": "integer",
                                "description": "Target number of charts to create",
                                "default": 3
                            },
                            "num_widgets": {
                                "type": "integer", 
                                "description": "Target number of interactive filter widgets",
                                "default": 2
                            },
                            "layout": {
                                "type": "string",
                                "description": "Layout name: feature_and_base, two_by_two, three_by_three, single_feature, etc.",
                                "default": "feature_and_base"
                            },
                            "theme": {
                                "type": "string",
                                "description": "Theme name: default, dark, rapids, rapids_dark",
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
                    "description": "Add additional charts to existing dashboard",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "chart_configs": {
                                "type": "string",
                                "description": "Description of charts to add: types, columns, and configurations"
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
                    "description": "Modify existing dashboard: change layout, theme, or chart properties",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "updates": {
                                "type": "string",
                                "description": "Description of modifications to apply"
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
                    "description": "Launch and display the interactive dashboard in browser or notebook",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "export_dashboard",
                    "description": "Export dashboard to HTML file for sharing or deployment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Output file path for HTML export",
                                "default": "dashboard_export.html"
                            }
                        }
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool: generate code -> run code -> store results."""
        
        # Get current state for context
        state_info = self.code_gen.get_state_description(self.global_state)
        
        # Generate code based on task and current state
        code = self.code_gen.generate_code(tool_name, state_info, **kwargs)
        
        # Execute the generated code
        result = self.code_execute.execute_code(code, self.global_state)
        
        # Update global state if execution succeeded
        if result['success']:
            self.global_state.update(result['globals'])
        
        # Store experiment for analysis
        experiment_data = {
            'task': tool_name,
            'parameters': kwargs,
            'code': code,
            'success': result['success'],
            'results': result.get('results', {}),
            'error': result.get('error')
        }
        self.store.save_experiment(experiment_data)
        
        # Format user-friendly response
        return self._format_response(tool_name, result)
    
    def _format_response(self, tool_name: str, result: Dict[str, Any]) -> str:
        """Format execution result for user display."""
        
        if not result['success']:
            # Error response
            return (
                f"✗ {tool_name} failed: {result['error']}\n\n"
                f"Traceback:\n{result.get('traceback', 'No traceback available')}"
            )
        
        # Success response
        parts = [f"✓ {tool_name} completed successfully\n"]
        
        # Add dashboard file location if available
        if result.get('dashboard_file'):
            parts.append(f"📊 Dashboard saved to: {result['dashboard_file']}\n")
        
        # Add dashboard info if created
        if result.get('dashboard'):
            parts.append(f"\ndashboard: {result['dashboard']}")
        
        # Add charts info if available
        if result.get('charts'):
            charts = result['charts']
            if isinstance(charts, list):
                parts.append(f"\ncharts: {len(charts)} chart(s) created")
            else:
                parts.append(f"\ncharts: {charts}")
        
        # Add widgets info if available
        if result.get('widgets'):
            widgets = result['widgets']
            if isinstance(widgets, list):
                parts.append(f"\nwidgets: {len(widgets)} widget(s) created")
            else:
                parts.append(f"\nwidgets: {widgets}")
        
        # Add output if available
        if result.get('output'):
            parts.append(f"\n\nOutput:\n{result['output']}")
        
        return "".join(parts)
    
    def get_experiment_summary(self) -> Dict[str, Any]:
        """Get summary of all experiments."""
        return self.store.get_experiment_summary()
    
    def get_recent_experiments(self, limit: int = 5) -> list:
        """Get recent experiments."""
        return self.store.get_recent_experiments(limit)