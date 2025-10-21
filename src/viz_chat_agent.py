# src/viz_chat_agent.py - Dashboard-focused visualization agent
import json
import os
from typing import Any, Dict, List

from src.tools.viz_exp_store import VizExperimentStore
from src.viz_tools import VizTools
from src import llm

class VizChatAgent:
    """A chat agent focused on building comprehensive cuxfilter dashboards."""
    
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
        
        # Uploaded files registry (for Streamlit integration)
        self.uploaded_files = {}
        
        # System message
        self.system_message = """You are a cuxfilter dashboard expert that generates custom Python code for interactive GPU-accelerated dashboards.

Your focus is on creating comprehensive dashboards with:
- Multiple chart types (scatter, bar, line, choropleth, heatmap, etc.)
- Interactive widgets (multi_select, drop_down, range_slider, etc.)
- Various layouts (feature_and_base, two_by_two, three_by_three, custom, etc.)
- Different themes (default, dark, rapids, rapids_dark)

Available tools:
- load_data(path) - Load dataset and convert to cudf
- describe_data() - Analyze dataset structure  
- create_dashboard(chart_types, layout, theme, sidebar_widgets) - Build complete dashboard
- add_charts(chart_configs) - Add more charts to existing dashboard
- customize_dashboard(updates) - Modify layout, theme, or chart properties
- show_dashboard() - Launch the dashboard
- export_dashboard(filepath) - Export to HTML/config
- show_history(limit) - View dashboard creation history

I generate complete cuxfilter dashboard code using cudf DataFrames for GPU acceleration."""

    def _show_history(self, limit: int = 5) -> str:
        """Show dashboard creation history."""
        experiments = self.store.get_recent_experiments(limit)
        
        if not experiments:
            return "No dashboard experiments found."
        
        output = f"Recent {len(experiments)} dashboards:\n\n"
        
        for i, exp in enumerate(experiments, 1):
            output += f"{i}. {exp.get('task', 'Unknown')}\n"
            output += f"   Date: {exp.get('date', 'Unknown')}\n"
            output += f"   Success: {exp.get('success', 'Unknown')}\n"
            
            results = exp.get('results', {})
            if results.get('num_charts'):
                output += f"   Charts: {results['num_charts']}\n"
            if results.get('layout'):
                output += f"   Layout: {results['layout']}\n"
            if results.get('theme'):
                output += f"   Theme: {results['theme']}\n"
            
            output += "\n"
        
        return output

    def _help(self) -> str:
        """Show available commands."""
        help_text = """Available Dashboard Commands:

Data Management:
• load_data(path) - Load CSV/Arrow/Parquet file
• describe_data() - Analyze columns and recommend charts

Dashboard Creation:
• create_dashboard(chart_types, layout, theme, sidebar_widgets)
  - Create comprehensive dashboard with multiple charts
  - Charts: scatter, bar, line, choropleth, heatmap, histogram, etc.
  - Layouts: feature_and_base, two_by_two, three_by_three, custom
  - Themes: default, dark, rapids, rapids_dark
  - Widgets: multi_select, drop_down, range_slider, date_range

Dashboard Management:
• add_charts(chart_configs) - Add more charts to dashboard
• customize_dashboard(updates) - Modify layout/theme/properties
• show_dashboard() - Launch interactive dashboard
• export_dashboard(filepath) - Save to HTML/config
• show_history(limit) - View creation history

Examples:
"load data data/auto_accidents.arrow"
"create dashboard with scatter map, bar charts for year and day, layout feature_and_base, theme rapids_dark"
"add charts: histogram for age, line chart for trend"
"customize dashboard: change theme to dark, layout to two_by_two"
"show dashboard"
"export dashboard to outputs/auto_accidents.html"

All commands generate complete cuxfilter code!
"""
        
        # Add uploaded files info if any
        if self.uploaded_files:
            help_text += "\n📁 Uploaded Files Available:\n"
            for name, path in self.uploaded_files.items():
                exists = "✅" if os.path.exists(path) else "❌"
                help_text += f"  • {name} {exists}\n"
        
        return help_text

    def _get_tool_specs(self) -> List[Dict]:
        """Get all tool specifications."""
        return self.viz_tools.get_tool_definitions() + [
            {
                "type": "function",
                "function": {
                    "name": "show_history",
                    "description": "Show dashboard creation history",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "default": 5}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "help",
                    "description": "Show available commands",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool function."""
        
        # Handle file path resolution for uploaded files
        if tool_name == 'load_data' and 'path' in arguments:
            path = arguments['path']
            
            # Check if this is an uploaded file (just filename, no path)
            if not os.path.exists(path) and hasattr(self, 'uploaded_files'):
                # Try to find in uploaded files
                if path in self.uploaded_files:
                    arguments['path'] = self.uploaded_files[path]
                    print(f"Resolved uploaded file: {path} -> {arguments['path']}")
                else:
                    # Try without extension
                    base_name = path.split('.')[0]
                    if base_name in self.uploaded_files:
                        arguments['path'] = self.uploaded_files[base_name]
                        print(f"Resolved uploaded file: {base_name} -> {arguments['path']}")
        
        # Handle dashboard tools
        if tool_name in ['load_data', 'describe_data', 'create_dashboard', 
                        'add_charts', 'customize_dashboard', 'show_dashboard',
                        'export_dashboard']:
            return self.viz_tools.execute_tool(tool_name, **arguments)
        
        # Handle utility tools
        elif tool_name == 'show_history':
            return self._show_history(arguments.get('limit', 5))
        
        elif tool_name == 'help':
            return self._help()
        
        else:
            return f"Unknown tool: {tool_name}"

    def chat(self, user_message: str) -> str:
        """Main chat method."""
        # Add system message if first message
        if not self.conversation:
            self.conversation.append({"role": "system", "content": self.system_message})
        
        # Add user message
        self.conversation.append({"role": "user", "content": user_message})
        
        try:
            # Get response from LLM
            response = self.llm_client.chat(
                messages=self.conversation,
                tools=self._get_tool_specs()
            )
            
            # Extract message
            message = response["choices"][0]["message"]
            
            # Check if LLM wants to use a tool
            if message.get("tool_calls"):
                tool_call = message["tool_calls"][0]
                tool_name = tool_call["function"]["name"]
                
                try:
                    arguments = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError:
                    arguments = {}
                
                # Call the tool
                result = self._call_tool(tool_name, arguments)
                
                # Add to conversation
                self.conversation.append({"role": "assistant", "content": result})
                
                return result
            
            # Regular text response
            else:
                content = message.get("content", "I'm not sure how to help with that.")
                self.conversation.append({"role": "assistant", "content": content})
                return content
                
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            self.conversation.append({"role": "assistant", "content": error_msg})
            return error_msg