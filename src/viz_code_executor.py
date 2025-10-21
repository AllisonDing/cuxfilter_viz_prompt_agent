# src/viz_code_executor.py - Safe code execution module for visualizations
import traceback
from typing import Any, Dict

def safe_execute_viz_code(code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Safely execute generated visualization code."""
    
    # Create safe execution environment
    safe_globals = {
        '__builtins__': {
            'print': print, 'len': len, 'range': range, 'enumerate': enumerate,
            'zip': zip, 'max': max, 'min': min, 'sum': sum, 'abs': abs,
            'round': round, 'float': float, 'int': int, 'str': str,
            'list': list, 'dict': dict, 'set': set, 'tuple': tuple,
            'sorted': sorted, 'isinstance': isinstance, 'type': type,
            'globals': lambda: safe_globals,
            'locals': lambda: safe_globals,
            '__import__': __import__,
            'hasattr': hasattr,
            'getattr': getattr,
            'setattr': setattr,
            'any': any,
            'all': all,
            'Exception': Exception,
            'open': open,
            'format': format,
            'divmod': divmod,
            'pow': pow,
            'map': map,
            'filter': filter,
            'reduce': lambda func, seq: __import__('functools').reduce(func, seq),
        },
        'results': {},  # Store results here
    }
    
    # Add context variables if provided
    if context:
        safe_globals.update(context)
    
    # Import base data libraries
    try:
        import pandas as pd
        import numpy as np
        safe_globals.update({'pd': pd, 'pandas': pd, 'np': np, 'numpy': np})
    except ImportError:
        pass
    
    # Import cudf for GPU dataframes
    try:
        import cudf
        safe_globals['cudf'] = cudf
    except ImportError:
        pass
    
    # Import cuxfilter and related libraries
    try:
        import cuxfilter
        from cuxfilter import charts, layouts, themes, DataFrame
        
        safe_globals.update({
            'cuxfilter': cuxfilter,
            'charts': charts,
            'layouts': layouts,
            'themes': themes,
            'DataFrame': DataFrame,
        })
    except ImportError:
        pass
    
    # Import bokeh components
    try:
        from bokeh.plotting import figure, output_file, save
        from bokeh.models import HoverTool, ColumnDataSource
        from bokeh.layouts import column, row, gridplot
        from bokeh import palettes
        
        safe_globals.update({
            'figure': figure,
            'output_file': output_file,
            'save': save,
            'HoverTool': HoverTool,
            'ColumnDataSource': ColumnDataSource,
            'column': column,
            'row': row,
            'gridplot': gridplot,
            'palettes': palettes,
        })
    except ImportError:
        pass
    
    # Import plotly for additional visualizations
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        safe_globals.update({
            'px': px,
            'go': go,
            'make_subplots': make_subplots,
            'plotly': go,
        })
    except ImportError:
        pass
    
    # Import matplotlib and seaborn (for fallback/static viz)
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        safe_globals.update({'plt': plt, 'sns': sns, 'matplotlib': plt})
    except ImportError:
        pass
    
    # Import data processing libraries
    try:
        from datetime import datetime, timedelta
        import json
        import os
        from pathlib import Path
        
        safe_globals.update({
            'datetime': datetime,
            'timedelta': timedelta,
            'json': json,
            'os': os,
            'Path': Path,
        })
    except ImportError:
        pass
    
    # Import holoviews for additional interactive viz
    try:
        import holoviews as hv
        import hvplot.pandas
        safe_globals.update({'hv': hv, 'hvplot': hvplot})
    except ImportError:
        pass
    
    # Import panel for dashboard widgets
    try:
        import panel as pn
        safe_globals['pn'] = pn
    except ImportError:
        pass
    
    # Import pyarrow for arrow file support
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        safe_globals.update({'pa': pa, 'pq': pq, 'pyarrow': pa})
    except ImportError:
        pass
    
    try:
        # Execute the code
        exec(code, safe_globals)
        
        return {
            'success': True,
            'results': safe_globals.get('results', {}),
            'globals': {k: v for k, v in safe_globals.items() 
                       if k not in ['__builtins__', 'results'] and not k.startswith('__')},
            'error': None,
            'code': code
        }
        
    except Exception as e:
        return {
            'success': False,
            'results': {},
            'globals': {},
            'error': str(e),
            'traceback': traceback.format_exc(),
            'code': code
        }