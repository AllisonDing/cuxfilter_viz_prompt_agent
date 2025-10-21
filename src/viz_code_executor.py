# # src/viz_code_executor.py - Safe code execution module for visualizations
# import traceback
# from typing import Any, Dict

# def safe_execute_viz_code(code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
#     """Safely execute generated visualization code."""
    
#     # Create safe execution environment
#     safe_globals = {
#         '__builtins__': {
#             'print': print, 'len': len, 'range': range, 'enumerate': enumerate,
#             'zip': zip, 'max': max, 'min': min, 'sum': sum, 'abs': abs,
#             'round': round, 'float': float, 'int': int, 'str': str,
#             'list': list, 'dict': dict, 'set': set, 'tuple': tuple,
#             'sorted': sorted, 'isinstance': isinstance, 'type': type,
#             'globals': lambda: safe_globals,
#             'locals': lambda: safe_globals,
#             '__import__': __import__,
#             'hasattr': hasattr,
#             'getattr': getattr,
#             'setattr': setattr,
#             'any': any,
#             'all': all,
#             'Exception': Exception,
#             'open': open,
#             'format': format,
#             'divmod': divmod,
#             'pow': pow,
#             'map': map,
#             'filter': filter,
#             'reduce': lambda func, seq: __import__('functools').reduce(func, seq),
#         },
#         'results': {},  # Store results here
#     }
    
#     # Add context variables if provided
#     if context:
#         safe_globals.update(context)
    
#     # Import base data libraries
#     try:
#         import pandas as pd
#         import numpy as np
#         safe_globals.update({'pd': pd, 'pandas': pd, 'np': np, 'numpy': np})
#     except ImportError:
#         pass
    
#     # Import cudf for GPU dataframes
#     try:
#         import cudf
#         safe_globals['cudf'] = cudf
#     except ImportError:
#         pass
    
#     # Import cuxfilter and related libraries
#     try:
#         import cuxfilter
#         from cuxfilter import charts, layouts, themes, DataFrame
        
#         safe_globals.update({
#             'cuxfilter': cuxfilter,
#             'charts': charts,
#             'layouts': layouts,
#             'themes': themes,
#             'DataFrame': DataFrame,
#         })
#     except ImportError:
#         pass
    
#     # Import bokeh components
#     try:
#         from bokeh.plotting import figure, output_file, save
#         from bokeh.models import HoverTool, ColumnDataSource
#         from bokeh.layouts import column, row, gridplot
#         from bokeh import palettes
        
#         safe_globals.update({
#             'figure': figure,
#             'output_file': output_file,
#             'save': save,
#             'HoverTool': HoverTool,
#             'ColumnDataSource': ColumnDataSource,
#             'column': column,
#             'row': row,
#             'gridplot': gridplot,
#             'palettes': palettes,
#         })
#     except ImportError:
#         pass
    
#     # Import plotly for additional visualizations
#     try:
#         import plotly.express as px
#         import plotly.graph_objects as go
#         from plotly.subplots import make_subplots
        
#         safe_globals.update({
#             'px': px,
#             'go': go,
#             'make_subplots': make_subplots,
#             'plotly': go,
#         })
#     except ImportError:
#         pass
    
#     # Import matplotlib and seaborn (for fallback/static viz)
#     try:
#         import matplotlib.pyplot as plt
#         import seaborn as sns
#         safe_globals.update({'plt': plt, 'sns': sns, 'matplotlib': plt})
#     except ImportError:
#         pass
    
#     # Import data processing libraries
#     try:
#         from datetime import datetime, timedelta
#         import json
#         import os
#         from pathlib import Path
        
#         safe_globals.update({
#             'datetime': datetime,
#             'timedelta': timedelta,
#             'json': json,
#             'os': os,
#             'Path': Path,
#         })
#     except ImportError:
#         pass
    
#     # Import holoviews for additional interactive viz
#     try:
#         import holoviews as hv
#         import hvplot.pandas
#         safe_globals.update({'hv': hv, 'hvplot': hvplot})
#     except ImportError:
#         pass
    
#     # Import panel for dashboard widgets
#     try:
#         import panel as pn
#         safe_globals['pn'] = pn
#     except ImportError:
#         pass
    
#     # Import pyarrow for arrow file support
#     try:
#         import pyarrow as pa
#         import pyarrow.parquet as pq
#         safe_globals.update({'pa': pa, 'pq': pq, 'pyarrow': pa})
#     except ImportError:
#         pass
    
#     try:
#         # Execute the code
#         exec(code, safe_globals)
        
#         return {
#             'success': True,
#             'results': safe_globals.get('results', {}),
#             'globals': {k: v for k, v in safe_globals.items() 
#                        if k not in ['__builtins__', 'results'] and not k.startswith('__')},
#             'error': None,
#             'code': code
#         }
        
#     except Exception as e:
#         return {
#             'success': False,
#             'results': {},
#             'globals': {},
#             'error': str(e),
#             'traceback': traceback.format_exc(),
#             'code': code
#         }

# viz_code_executor.py
import sys
import io
import traceback
import contextlib
import os
import datetime
from typing import Dict, Any

class VizCodeExecutor:
    """Executes visualization code safely."""
    
    def __init__(self, df = None):
        """Initialize with the dataframe to visualize."""
        self.df = df
        self.cux_df = None
        
    def execute_code(self, code: str, global_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the generated visualization code."""

        if global_state is None:
            global_state = {}
        
        # Prepare namespace with required imports and data
        local_vars = {
            'df': self.df,
            'cux_df': self.cux_df,
            **global_state # Add global state variables
        }
        
        captured_output = []
        
        # Capture stdout
        output_buffer = io.StringIO()
        
        try:
            with contextlib.redirect_stdout(output_buffer):
                # Execute the code
                exec(code, globals(), local_vars)
            
            # Get captured output
            output_text = output_buffer.getvalue()
            if output_text:
                captured_output.append(output_text)
            
            # ⭐ NEW SECTION: Export dashboard if created ⭐
            # Check if a dashboard was created and export it
            if 'dashboard' in local_vars:
                dashboard = local_vars['dashboard']
                
                # Create output directory if it doesn't exist
                output_dir = "dashboards"
                os.makedirs(output_dir, exist_ok=True)
                
                # Generate filename with timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(output_dir, f"dashboard_{timestamp}.html")
                
                # Export dashboard to HTML
                try:
                    dashboard.export(output_file)
                    captured_output.append(f"\n✓ Dashboard exported to: {output_file}")
                    local_vars['_dashboard_file'] = output_file
                except Exception as e:
                    captured_output.append(f"\n✗ Failed to export dashboard: {str(e)}")
            # ⭐ END OF NEW SECTION ⭐
            
            # Store the cux_df if it was created
            if 'cux_df' in local_vars and local_vars['cux_df'] is not None:
                self.cux_df = local_vars['cux_df']

            # Store df if it was updated
            if 'df' in local_vars and local_vars['df'] is not None:
                self.df = local_vars['df']
            
            # Return success result
            return {
                "success": True,
                "output": "\n".join(captured_output),
                "dashboard": local_vars.get('dashboard'),
                "dashboard_file": local_vars.get('_dashboard_file'),  # ⭐ NEW LINE ⭐
                "charts": local_vars.get('charts'),
                "widgets": local_vars.get('widgets'),
                "cux_df": local_vars.get('cux_df'),
                "globals": local_vars # Return all variables for state management
            }
            
        except Exception as e:
            # Capture the full traceback
            error_traceback = traceback.format_exc()
            
            return {
                "success": False,
                "error": str(e),
                "traceback": error_traceback,
                "output": output_buffer.getvalue(),
                "globals": {}
            }
        
        finally:
            output_buffer.close()
    
    def get_dataframe_info(self) -> Dict[str, Any]:
        """Get information about the loaded dataframe."""
        if self.df is None:
            return {"error": "No dataframe loaded"}
        
        return {
            "shape": self.df.shape,
            "columns": list(self.df.columns),
            "dtypes": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
            "head": self.df.head().to_dict(),
            "missing_values": self.df.isnull().sum().to_dict()
        }