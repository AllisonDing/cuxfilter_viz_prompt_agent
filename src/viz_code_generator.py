# src/viz_code_generator.py - Dashboard-focused code generation
import re
from typing import Dict, Any
from src import llm

class VizCodeGenerator:
    """Generates comprehensive cuxfilter dashboard code using LLM."""
    
    def __init__(self):
        self.llm_client = llm.create_client()
        
        # Task-specific prompts focused on dashboard building
        self.task_prompts = {
            "load_data": """Generate Python code to load dataset from '{path}' and prepare for cuxfilter dashboard.
            
Requirements:
- Load file using appropriate method (CSV, Arrow, Parquet)
- Convert pandas DataFrame to cudf DataFrame for GPU acceleration
- Create cuxfilter.DataFrame object
- Analyze columns: identify numeric, categorical, datetime, lat/lon columns
- Store as 'cux_df' for dashboard creation
- Store results dict with keys: 'success', 'message', 'shape', 'columns', 'dtypes', 'column_types'
- Handle file not found errors

Example structure:
```python
import pandas as pd
import cudf
import cuxfilter

# Load data
df = pd.read_csv(path) # or read_arrow, read_parquet
gdf = cudf.DataFrame.from_pandas(df)
cux_df = cuxfilter.DataFrame.from_dataframe(gdf)

# Analyze columns
results = {{
    'success': True,
    'message': 'Data loaded successfully',
    'shape': cux_df.data.shape,
    'columns': list(cux_df.data.columns),
    'dtypes': dict(cux_df.data.dtypes),
    'column_types': {{
        'numeric': [...],
        'categorical': [...],
        'datetime': [...]
    }}
}}
```""",
            
            "describe_data": """Generate Python code to analyze the cuxfilter DataFrame and recommend dashboard components.
            
Requirements:
- Analyze cux_df.data columns and data types ONLY
- DO NOT create any charts or widgets - just analyze the data
- Identify best chart types for each column (as recommendations, not actual charts)
- Recommend layout based on number of charts
- Suggest appropriate widgets for filtering
- Provide theme recommendations
- Store comprehensive results dict with analysis and recommendations

Output should include:
- Column statistics (min, max, mean, std, null_count)
- Recommended chart types for each column (as text strings, not actual objects)
- Suggested layout name
- Widget recommendations (as text list, not actual widgets)
- Theme suggestion

DO NOT EXECUTE ANY CHART CREATION CODE - ONLY ANALYZE AND RECOMMEND!

Example output structure:
```python
results = {
    'column_stats': {
        'column1': {'min': ..., 'max': ..., 'mean': ...},
        'column2': {...}
    },
    'recommended_charts': {
        'column1': {'type': 'bar', 'reason': 'categorical data'},
        'column2': {'type': 'scatter', 'reason': 'spatial coordinates'}
    },
    'suggested_layout': 'feature_and_base',
    'widget_recommendations': ['range_slider for trip_distance', 'date_range_slider for datetime'],
    'theme_suggestion': 'rapids_dark'
}
```""",
            
            "create_dashboard": """Generate complete Python code to create a comprehensive cuxfilter dashboard.

Configuration:
{config}

Requirements:
- Import necessary modules: cuxfilter, charts, layouts, themes, palettes
- Use existing cux_df (cudf DataFrame wrapped in cuxfilter.DataFrame)
- Create {num_charts} charts based on specified types and columns
- Chart types available: scatter, bar, line, choropleth, heatmap, histogram, number
- Configure charts with appropriate parameters (colors, aggregations, etc.)
- Create {num_widgets} sidebar widgets (multi_select, drop_down, range_slider)
- Apply layout: {layout} (or custom layout_array if specified)
- Apply theme: {theme} (default, dark, rapids, rapids_dark)
- Create dashboard with d = cux_df.dashboard(charts_list, sidebar=widgets, layout=..., theme=..., title=...)
- Store dashboard as 'd' globally
- Store results dict with dashboard info

Chart Examples - ONLY USE THESE REAL CUXFILTER APIS:
```python
# Scatter (datashader or bokeh) - NO data_points parameter!
chart1 = cuxfilter.charts.scatter(
    x='lon', y='lat', 
    aggregate_col='value', aggregate_fn='mean',
    color_palette=['#3182bd', '#6baed6', '#ff0068'],
    tile_provider='CartoLight',
    pixel_shade_type='linear'
)

# Bar chart - column name and optional data_points
chart2 = cuxfilter.charts.bar('category', data_points=50)

# Line chart - x and y columns, NO aggregate_fn!
chart3 = cuxfilter.charts.line(x='date', y='value')

# Choropleth map
chart4 = cuxfilter.charts.choropleth(
    x='zip', 
    color_column='value',
    color_aggregate_fn='mean',
    geo_color_palette=palettes.Purples9,
    geoJSONSource='url_to_geojson'
)

# Heatmap
chart5 = cuxfilter.charts.heatmap(
    x='x_col', 
    y='y_col', 
    aggregate_col='value', 
    aggregate_fn='mean'
)

# Number widget (KPI)
chart6 = cuxfilter.charts.number(
    expression="column", 
    aggregate_fn="mean",
    title="Average Value"
)
```

REAL WIDGETS - ONLY USE THESE:
```python
# Range slider - for numeric columns
widget1 = cuxfilter.charts.range_slider('numeric_col', data_points=50)

# Date range slider - for datetime columns  
widget2 = cuxfilter.charts.date_range_slider('datetime_col')

# Dropdown - for categorical columns
widget3 = cuxfilter.charts.drop_down('category_col')

# Multi-select - for categorical columns
widget4 = cuxfilter.charts.multi_select('category_col')

# Int slider - for integer columns
widget5 = cuxfilter.charts.int_slider('int_col')

# Float slider - for float columns
widget6 = cuxfilter.charts.float_slider('float_col')
```

CRITICAL - CHARTS/WIDGETS THAT DO NOT EXIST:
- NO histogram chart (does not exist in cuxfilter)
- NO date_range widget (use date_range_slider instead)
- scatter() has NO data_points parameter
- line() has NO aggregate_fn parameter

ONLY USE:
- Charts: scatter, bar, line, choropleth, heatmap, number
- Widgets: range_slider, date_range_slider, drop_down, multi_select, int_slider, float_slider

Widget Examples:
```python
widget1 = cuxfilter.charts.multi_select('category')
widget2 = cuxfilter.charts.drop_down('region')
widget3 = cuxfilter.charts.range_slider('value', data_points=50)
widget4 = cuxfilter.charts.date_range('date_column')
```

Layouts:
- cuxfilter.layouts.single_feature
- cuxfilter.layouts.feature_and_base  
- cuxfilter.layouts.double_feature
- cuxfilter.layouts.two_by_two
- cuxfilter.layouts.feature_and_triple_base
- cuxfilter.layouts.three_by_three
- Custom: layout_array=[[1,1,2],[3,4,4]]

Themes:
- cuxfilter.themes.default
- cuxfilter.themes.dark
- cuxfilter.themes.rapids
- cuxfilter.themes.rapids_dark

Create a complete, functional dashboard with all specified components!""",
            
            "add_charts": """Generate Python code to add new charts to the existing dashboard 'd'.

Charts to add:
{chart_configs}

Requirements:
- Create new chart objects based on specifications
- Use cuxfilter.charts.* for chart creation
- Call d.add_charts(charts=[new_charts], sidebar=[new_widgets]) to add to dashboard
- Update results dict with newly added charts

Available chart types: scatter, bar, line, choropleth, heatmap, histogram, number, etc.""",
            
            "customize_dashboard": """Generate Python code to customize the existing dashboard 'd'.

Updates requested:
{updates}

Requirements:
- Modify dashboard properties (layout, theme, chart configurations)
- For layout change: recreate dashboard with new layout
- For theme change: update dashboard theme
- For chart updates: modify chart properties
- Store results dict with applied changes

Note: Some changes may require recreating the dashboard object.""",
            
            "show_dashboard": """Generate Python code to launch the cuxfilter dashboard.

Requirements:
- Use d.app() for inline notebook display OR d.show() for remote display
- Default to d.app() for inline display
- Store results dict with dashboard status and access info

Example:
```python
# Launch dashboard inline
d.app()

results = {{
    'success': True,
    'message': 'Dashboard launched successfully',
    'mode': 'inline',
    'note': 'Dashboard running in notebook cell'
}}
```

Or for remote:
```python
# Launch dashboard remotely
dashboard_link = d.show()

results = {{
    'success': True, 
    'message': 'Dashboard launched successfully',
    'mode': 'remote',
    'url': dashboard_link
}}
```""",
            
            "export_dashboard": """Generate Python code to export the dashboard to '{filepath}'.

Requirements:
- Export dashboard configuration or static HTML
- Save to specified filepath
- Ensure directory exists
- Store results dict with export details

Methods:
1. Export queried data: queried_df = d.export()
2. Save dashboard config to file
3. Export static HTML if possible""",
        }
    
    def generate_code(self, task_name: str, state_info: str, **kwargs) -> str:
        """Generate Python code for a dashboard task."""
        
        # Get task-specific prompt
        prompt_template = self.task_prompts.get(task_name, "")
        
        if not prompt_template:
            return f"# Error: Unknown task '{task_name}'\nresults = {{'error': 'Unknown task'}}"
        
        # Format the prompt with provided arguments
        try:
            task_prompt = prompt_template.format(**kwargs)
        except KeyError as e:
            task_prompt = prompt_template
        
        full_prompt = f"""Current State:
{state_info}

Task: {task_prompt}

Generate complete, executable Python code that:
1. Works with current global variables (cux_df, d, etc.)
2. Uses cuxfilter for GPU-accelerated dashboards
3. Uses cudf DataFrames for data
4. Handles errors gracefully
5. Stores ALL results in the 'results' dictionary
6. Includes helpful print statements
7. Creates production-ready, interactive dashboards
8. Follows cuxfilter best practices

IMPORTANT:
- Use proper imports: import cuxfilter, from cuxfilter import charts, layouts, themes
- Use from bokeh import palettes for color palettes
- Ensure all chart configurations are valid
- Match column names exactly from the dataframe

Return ONLY executable Python code with NO markdown formatting, NO explanations, NO ```python blocks."""
        
        try:
            response = self.llm_client.chat([
                {"role": "system", "content": "You are an expert cuxfilter dashboard developer. Generate ONLY executable Python code with no formatting or explanations. Follow cuxfilter API exactly as documented."},
                {"role": "user", "content": full_prompt}
            ])
            
            code = response["choices"][0]["message"]["content"]
            
            # Clean up code - remove markdown formatting
            code = re.sub(r'^```python\s*\n', '', code)
            code = re.sub(r'^```\s*\n', '', code)
            code = re.sub(r'\n```$', '', code)
            code = code.strip()
            
            return code
            
        except Exception as e:
            return f"# Error generating code: {str(e)}\nresults = {{'error': 'Code generation failed'}}"
    
    def get_state_description(self, global_state: Dict[str, Any]) -> str:
        """Get description of current state for code generation."""
        state_desc = "Current Global State:\n"
        
        if 'cux_df' in global_state:
            cux_df = global_state['cux_df']
            try:
                shape = cux_df.data.shape
                columns = list(cux_df.data.columns)
                dtypes = dict(cux_df.data.dtypes)
                state_desc += f"- cux_df: cuxfilter.DataFrame with shape {shape}\n"
                state_desc += f"- cux_df.data.columns: {columns}\n"
                state_desc += f"- cux_df.data.dtypes: {dtypes}\n"
            except:
                state_desc += "- cux_df: cuxfilter.DataFrame exists\n"
        else:
            state_desc += "- cux_df: Not loaded\n"
        
        if 'd' in global_state:
            state_desc += f"- d: cuxfilter dashboard exists\n"
            try:
                dashboard = global_state['d']
                if hasattr(dashboard, '_charts'):
                    state_desc += f"- d._charts: {len(dashboard._charts)} charts\n"
            except:
                pass
        else:
            state_desc += "- d: Dashboard not created\n"
        
        # Add any other relevant state info
        for key, value in global_state.items():
            if key not in ['cux_df', 'd', '__builtins__', 'results']:
                state_desc += f"- {key}: {type(value).__name__}\n"
        
        return state_desc