# src/viz_chat_agent.py - Pure documentation-based chat agent
import json
import os
from typing import Any, Dict, List

from src.tools.viz_exp_store import VizExperimentStore
from src.viz_tools import VizTools
from src import llm

class VizChatAgent:
    """Chat agent that builds cuxfilter dashboards using pure API specifications."""
    
    def __init__(self):
        # Storage for dashboard experiments
        self.store = VizExperimentStore()
        self.store.clear_all()
        
        # AI client
        self.llm_client = llm.create_client()
        
        # Dashboard tools handler
        self.viz_tools = VizTools(self.store)
        
        # Conversation memory
        self.conversation = []
        
        # Uploaded files registry
        self.uploaded_files = {}
        
        # Track if data is loaded
        self.data_loaded = False
        
        # System message - pure documentation style
        self.system_message = """You are a cuxfilter dashboard expert that uses function calling to create GPU-accelerated interactive visualizations.

AVAILABLE TOOLS:
- load_data(path) - Load and prepare dataset from CSV/Arrow/Parquet
- describe_data() - Analyze dataset and recommend visualizations
- create_dashboard(config, num_charts, num_widgets, layout, theme) - Build complete dashboard
- add_charts(chart_configs) - Add more visualizations to dashboard
- customize_dashboard(updates) - Modify layout, theme, or properties
- show_dashboard() - Launch interactive dashboard
- export_dashboard(filepath) - Save to HTML file
- show_history(limit) - View creation history

CUXFILTER CAPABILITIES:
Chart Types: scatter (with map tiles), bar, line, number (KPIs), choropleth, heatmap
Widget Types: range_slider, date_range_slider, multi_select, drop_down
Layouts: feature_and_base, two_by_two, three_by_three, single_feature, double_feature, custom
Themes: default, dark, rapids, rapids_dark

WORKFLOW:
1. User uploads/specifies data file
2. Call load_data(path) to prepare dataset
3. Optionally call describe_data() to analyze structure
4. Call create_dashboard() with natural language config
5. Optionally add more charts or customize
6. Dashboard is automatically exported to HTML

BEHAVIOR:
- Always call appropriate tools rather than just explaining
- Use natural language in config parameters
- Tools generate and execute Python code automatically
- Handle errors gracefully and retry if needed
- Provide clear feedback about what was created"""

    def _show_history(self, limit: int = 5) -> str:
        """Show dashboard creation history."""
        experiments = self.store.get_recent_experiments(limit)
        
        if not experiments:
            return "No dashboard experiments found in history."
        
        lines = [f"Recent {len(experiments)} operations:\n"]
        
        for i, exp in enumerate(experiments, 1):
            task = exp.get('task', 'Unknown')
            date = exp.get('date', 'Unknown')
            success = '✓' if exp.get('success') else '✗'
            
            lines.append(f"{i}. {success} {task} - {date}")
            
            results = exp.get('results', {})
            if results.get('shape'):
                lines.append(f"   Data: {results['shape'][0]:,} rows × {results['shape'][1]} cols")
            if results.get('num_charts'):
                lines.append(f"   Charts: {results['num_charts']}")
            if results.get('dashboard_file'):
                lines.append(f"   File: {results['dashboard_file']}")
        
        return "\n".join(lines)

    def _help(self) -> str:
        """Show available capabilities and current state."""
        help_sections = []
        
        # Core capabilities
        help_sections.append("""DASHBOARD AGENT CAPABILITIES:

Data Operations:
  load_data(path) - Load CSV, Arrow, or Parquet file
  describe_data() - Analyze columns and get recommendations

Dashboard Creation:
  create_dashboard(config, ...) - Build interactive dashboard
    • Specify chart types and columns in natural language
    • Choose layout: feature_and_base, two_by_two, three_by_three
    • Select theme: default, dark, rapids, rapids_dark
    • Add widgets: range_slider, multi_select, date_range_slider

Dashboard Management:
  add_charts(chart_configs) - Add more visualizations
  customize_dashboard(updates) - Modify appearance or behavior
  show_dashboard() - Launch in browser/notebook
  export_dashboard(filepath) - Save to HTML

Utilities:
  show_history(limit) - View recent operations
  help - Show this help message

CHART TYPES AVAILABLE:
  scatter - Scatter plot (supports map tiles for geospatial)
  bar - Bar chart (for categorical or binned continuous data)
  line - Line chart (for time series or trends)
  number - KPI/metric display
  choropleth - Geographic choropleth map
  heatmap - 2D heatmap visualization

WIDGET TYPES AVAILABLE:
  range_slider - Filter numeric ranges
  date_range_slider - Filter date/time ranges
  multi_select - Select multiple categories
  drop_down - Select single category""")
        
        # Current state
        if self.uploaded_files:
            help_sections.append("\nAVAILABLE DATA FILES:")
            for name, path in self.uploaded_files.items():
                exists = "✅" if os.path.exists(path) else "❌"
                help_sections.append(f"  {exists} {name}")
                help_sections.append(f"     Path: {path}")
        
        # Data loaded status
        if self.data_loaded:
            help_sections.append("\n✅ DATA LOADED - Ready to create dashboards")
        else:
            help_sections.append("\n⚠️  NO DATA LOADED - Use load_data(path) first")
        
        # Quick start
        help_sections.append("""
QUICK START:
  1. "load data from <filename>"
  2. "create dashboard with scatter map and bar charts"
  3. Dashboard automatically exports to dashboards/ folder""")
        
        return "\n".join(help_sections)

    def _get_tool_specs(self) -> List[Dict]:
        """Get all tool specifications."""
        return self.viz_tools.get_tool_definitions() + [
            {
                "type": "function",
                "function": {
                    "name": "show_history",
                    "description": "Show recent dashboard creation operations and their outcomes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Number of recent operations to show",
                                "default": 5
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "help",
                    "description": "Show available capabilities, current state, and usage instructions",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool function."""
        
        # Handle file path resolution for uploaded files
        if tool_name == 'load_data' and 'path' in arguments:
            path = arguments['path']
            
            # Check if this is a reference to an uploaded file
            if not os.path.exists(path) and self.uploaded_files:
                # Try exact match
                if path in self.uploaded_files:
                    arguments['path'] = self.uploaded_files[path]
                    print(f"Resolved uploaded file: {path} -> {arguments['path']}")
                else:
                    # Try without extension
                    base_name = path.split('.')[0]
                    if base_name in self.uploaded_files:
                        arguments['path'] = self.uploaded_files[base_name]
                        print(f"Resolved uploaded file: {base_name} -> {arguments['path']}")
        
        # Route to appropriate handler
        if tool_name in ['load_data', 'describe_data', 'create_dashboard', 
                        'add_charts', 'customize_dashboard', 'show_dashboard',
                        'export_dashboard']:
            result = self.viz_tools.execute_tool(tool_name, **arguments)
            
            # Track data loading status
            if tool_name == 'load_data' and '✓' in result:
                self.data_loaded = True
            
            return result
        
        elif tool_name == 'show_history':
            return self._show_history(arguments.get('limit', 5))
        
        elif tool_name == 'help':
            return self._help()
        
        else:
            return f"Unknown tool: {tool_name}\n\nUse 'help' to see available tools."

    def chat(self, user_message: str) -> str:
        """Main chat interface."""
        
        # Initialize conversation with system message
        if not self.conversation:
            self.conversation.append({
                "role": "system", 
                "content": self.system_message
            })
        
        # Add user message
        self.conversation.append({
            "role": "user", 
            "content": user_message
        })
        
        try:
            # Get LLM response with tool calling
            response = self.llm_client.chat(
                messages=self.conversation,
                tools=self._get_tool_specs()
            )
            
            # Extract response message
            message = response["choices"][0]["message"]
            
            # Check if LLM wants to use tools
            if message.get("tool_calls"):
                # Execute first tool call
                tool_call = message["tool_calls"][0]
                tool_name = tool_call["function"]["name"]
                
                # Parse arguments
                try:
                    arguments = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError:
                    arguments = {}
                
                # Execute tool
                result = self._call_tool(tool_name, arguments)
                
                # Add to conversation history
                self.conversation.append({
                    "role": "assistant", 
                    "content": result
                })
                
                return result
            
            # Regular text response (no tool call)
            else:
                content = message.get("content", "I'm not sure how to help with that. Try 'help' to see what I can do.")
                
                self.conversation.append({
                    "role": "assistant", 
                    "content": content
                })
                
                return content
                
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}\n\nPlease try rephrasing your request or use 'help' for guidance."
            
            self.conversation.append({
                "role": "assistant", 
                "content": error_msg
            })
            
            return error_msg
    
    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation = []
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get current agent state summary."""
        return {
            "data_loaded": self.data_loaded,
            "uploaded_files": list(self.uploaded_files.keys()),
            "conversation_length": len(self.conversation),
            "experiment_count": self.store.count_experiments()
        }