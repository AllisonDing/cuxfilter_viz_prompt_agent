# src/viz_code_executor.py - Minimal executor with no hardcoded logic
import sys
import io
import traceback
import contextlib
import os
import datetime
from typing import Dict, Any

class VizCodeExecutor:
    """Executes visualization code safely with minimal intervention."""
    
    def __init__(self, df=None):
        """Initialize with optional dataframe."""
        self.df = df
        self.cux_df = None
        
    def execute_code(self, code: str, global_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute generated code with no modifications."""
        
        if global_state is None:
            global_state = {}
        
        # Prepare execution namespace
        local_vars = {
            'df': self.df,
            'cux_df': self.cux_df,
            'results': {},  # Always provide empty results dict
            **global_state
        }
        
        # Capture output
        output_buffer = io.StringIO()
        captured_output = []
        
        try:
            # Execute code
            with contextlib.redirect_stdout(output_buffer):
                exec(code, globals(), local_vars)
            
            # Get output
            output_text = output_buffer.getvalue()
            if output_text:
                captured_output.append(output_text)
            
            # Extract results
            results = local_vars.get('results', {})
            
            # Update instance state
            if 'cux_df' in local_vars and local_vars['cux_df'] is not None:
                self.cux_df = local_vars['cux_df']
            
            if 'df' in local_vars and local_vars['df'] is not None:
                self.df = local_vars['df']
            
            # Check if dashboard was created
            dashboard = local_vars.get('d') or local_vars.get('dashboard')
            dashboard_file = None
            
            if dashboard:
                # Try to export if dashboard exists
                dashboard_file = self._try_export_dashboard(dashboard, captured_output)
                if dashboard_file:
                    results['dashboard_file'] = dashboard_file
            
            return {
                "success": True,
                "output": "\n".join(captured_output),
                "results": results,
                "dashboard": dashboard,
                "dashboard_file": dashboard_file,
                "charts": local_vars.get('charts') or local_vars.get('charts_list'),
                "widgets": local_vars.get('widgets') or local_vars.get('widgets_list'),
                "cux_df": local_vars.get('cux_df'),
                "globals": local_vars
            }
            
        except Exception as e:
            error_traceback = traceback.format_exc()
            
            return {
                "success": False,
                "error": str(e),
                "traceback": error_traceback,
                "output": output_buffer.getvalue(),
                "results": {},
                "globals": {}
            }
        
        finally:
            output_buffer.close()
    
    def _try_export_dashboard(self, dashboard, captured_output: list) -> str:
        """Attempt to export dashboard to HTML file."""
        try:
            output_dir = "dashboards"
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"dashboard_{timestamp}.html")
            
            # Try different export methods (cuxfilter API has changed over versions)
            try:
                # Method 1: export() returns HTML content
                html_content = dashboard.export()
                with open(output_file, 'w') as f:
                    f.write(html_content)
            except TypeError:
                # Method 2: export() takes filename
                dashboard.export(output_file)
            except Exception:
                # Method 3: Use save() if it exists
                if hasattr(dashboard, 'save'):
                    dashboard.save(output_file)
                else:
                    raise
            
            captured_output.append(f"\n✓ Dashboard exported to: {output_file}")
            return output_file
            
        except Exception as e:
            captured_output.append(f"\n✗ Export failed: {str(e)}")
            return None
    
    def get_dataframe_info(self) -> Dict[str, Any]:
        """Get information about the loaded dataframe."""
        if self.df is None:
            return {"error": "No dataframe loaded"}
        
        try:
            return {
                "shape": self.df.shape,
                "columns": list(self.df.columns),
                "dtypes": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
                "head": self.df.head().to_dict(),
                "missing_values": self.df.isnull().sum().to_dict()
            }
        except Exception as e:
            return {"error": str(e)}