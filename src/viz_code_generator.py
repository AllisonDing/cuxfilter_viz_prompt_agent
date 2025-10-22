# src/viz_code_generator.py - Pure API documentation approach (NO code examples)

import re
from typing import Dict, Any
from src import llm

class VizCodeGenerator:
    """Generates cuxfilter dashboard code from API documentation only."""
    
    def __init__(self):
        self.llm_client = llm.create_client()
        
        # Pure API documentation (no code examples)
        self.api_specs = {
            "cuxfilter_api": """
cuxfilter API Specification:

DATAFRAME:
- cuxfilter.DataFrame.from_dataframe(cudf_df) -> Returns cuxfilter.DataFrame object
- cux_df.data -> Access underlying cudf DataFrame
- cux_df.data.columns -> List of column names
- cux_df.data[col].dtype -> Get column data type
- cux_df.dashboard(charts=[], sidebar=[], layout=layout_obj, theme=theme_obj, title=str) -> Create dashboard

CHART TYPES (cuxfilter.charts.*):

1. scatter - For 2D scatter plots (especially spatial/geographic data)
   SIGNATURE: charts.scatter(x, y, aggregate_col=None, aggregate_fn=None, 
                            color_palette=None, tile_provider=None, pixel_shade_type=None)
   REQUIRED: x (str), y (str) - column names for x and y axes
   OPTIONAL: aggregate_col (str) - column to aggregate for coloring
            aggregate_fn (str) - 'mean', 'sum', 'count', 'min', 'max'
            color_palette (list) - e.g., palettes.Viridis256
            tile_provider (str) - 'CartoLight', 'ESRI', etc. for map background
            pixel_shade_type (str) - 'linear', 'log', 'cbrt'
   CRITICAL: Does NOT accept 'data_points' parameter
   USAGE: charts.scatter(x='longitude', y='latitude', aggregate_col='value', aggregate_fn='mean')

2. bar - For categorical data or binned continuous data
   SIGNATURE: charts.bar(x, data_points=None)
   REQUIRED: x (str) - column name (this is the ONLY required parameter, NOT 'column')
   OPTIONAL: data_points (int) - number of bins for continuous data
   CRITICAL: Parameter name is 'x', not 'column'
   USAGE: charts.bar(x='category_column')
          charts.bar(x='continuous_column', data_points=50)

3. line - For time series or trend data
   SIGNATURE: charts.line(x, y)
   REQUIRED: x (str), y (str) - column names
   CRITICAL: Does NOT accept 'aggregate_fn' parameter
   USAGE: charts.line(x='date', y='value')

4. number - For KPI/metric display
   SIGNATURE: charts.number(expression, aggregate_fn, title)
   REQUIRED: expression (str) - column name
            aggregate_fn (str) - 'mean', 'sum', 'count', etc.
            title (str) - display title
   USAGE: charts.number(expression='revenue', aggregate_fn='sum', title='Total Revenue')

5. choropleth - For geographic choropleth maps
   SIGNATURE: charts.choropleth(x, color_column, color_aggregate_fn, 
                                geo_color_palette, geoJSONSource)
   REQUIRED: All parameters required
   USAGE: Rarely used - requires GeoJSON data

6. heatmap - For 2D heatmaps
   SIGNATURE: charts.heatmap(x, y, aggregate_col, aggregate_fn)
   REQUIRED: All parameters required
   USAGE: charts.heatmap(x='hour', y='day', aggregate_col='count', aggregate_fn='sum')

INVALID CHART TYPES (DO NOT USE):
- histogram (does not exist - use bar instead)

WIDGETS (cuxfilter.charts.*):
1. range_slider(column: str, data_points: int = None)
2. date_range_slider(column: str)
3. drop_down(column: str)
4. multi_select(column: str)
5. int_slider(column: str)
6. float_slider(column: str)

LAYOUTS (cuxfilter.layouts.*):
- single_feature, double_feature, triple_feature
- feature_and_base, feature_and_double_base, feature_and_triple_base
- two_by_two, three_by_three
- Custom: layout_array=[[chart_indices]]

THEMES (cuxfilter.themes.*):
- default, dark, rapids, rapids_dark

DATA LOADING:
- pandas: pd.read_csv(), pd.read_parquet(), pd.read_feather()
- cudf: cudf.DataFrame.from_pandas(df)
- cuxfilter: cuxfilter.DataFrame.from_dataframe(gdf)

COLUMN ANALYSIS:
- dtype checks: 'int' in dtype, 'float' in dtype, 'datetime' in dtype
- Use for loops to iterate: for col in columns
- String methods: str(dtype), col.lower()
""",
            
            "requirements": """
CODE REQUIREMENTS:

1. ALWAYS initialize results dictionary first:
   results = {'success': False}

2. Use try-except blocks for error handling

3. Print informative status messages

4. Store outputs in results dictionary

5. For column iteration:
   - Use simple for loops: for col in cux_df.data.columns
   - Define all variables inside loop before use
   - Use temporary variables for clarity

6. Avoid:
   - Generator expressions with undefined variables
   - List comprehensions with external variables
   - Lambda functions with closure issues

7. Type conversions:
   - Use str(), float(), int(), list() explicitly
   - Don't assume automatic type coercion

8. String operations:
   - Use + for concatenation
   - Use str.format() or f-strings carefully
   - Always convert to string before concatenation
"""
        }
    
    def generate_code(self, task_name: str, state_info: str, **kwargs) -> str:
        """Generate code from API documentation only."""
        
        # Task-specific instructions (no code examples)
        task_instructions = {
            "load_data": f"""
Task: Load data from file path: {kwargs.get('path', 'UNKNOWN')}

Steps required:
1. Import required modules: pandas, cudf, cuxfilter, os
2. Initialize results dictionary with keys: success, message, shape, columns, dtypes, column_types
3. Check if file exists using os.path.exists()
4. Load file based on extension (.csv/.parquet/.arrow)
5. Convert pandas DataFrame to cudf DataFrame
6. Create cuxfilter.DataFrame from cudf DataFrame
7. Analyze columns and categorize by type (numeric, categorical, datetime, spatial)
8. Store all results in results dictionary
9. Print status messages
10. Handle errors with try-except

File path: {kwargs.get('path', '')}
""",
            
            "describe_data": """
Task: Analyze cuxfilter DataFrame and recommend visualizations

Steps required:
1. Initialize results dictionary with keys: column_stats, recommended_charts, suggested_layout, widget_recommendations, theme_suggestion
2. Iterate through cux_df.data.columns
3. For each column, calculate statistics based on dtype
4. Recommend appropriate chart type based on data characteristics
5. Suggest layout based on number of columns
6. Recommend widgets for filtering
7. Store all results in results dictionary
""",
            
            "create_dashboard": f"""
Task: Create cuxfilter dashboard

Configuration: {kwargs.get('config', '')}
Layout: {kwargs.get('layout', 'feature_and_base')}
Theme: {kwargs.get('theme', 'rapids_dark')}
Number of charts: {kwargs.get('num_charts', 3)}
Number of widgets: {kwargs.get('num_widgets', 2)}

Steps required:
1. Import cuxfilter, charts, layouts, themes, palettes
2. Initialize results dictionary
3. Create empty lists for charts and widgets
4. Analyze available columns in cux_df.data
5. Create appropriate charts based on column types
6. Create appropriate widgets for filtering
7. Call cux_df.dashboard() with all parameters
8. Store dashboard object and metadata in results
9. Ensure dashboard variable is also stored for export

CRITICAL PARAMETER RULES - FOLLOW EXACTLY:
- charts.scatter(x='col1', y='col2') - x and y are REQUIRED, both are column names
- charts.bar(x='col1') - parameter name is 'x', NOT 'column', it is REQUIRED
- charts.line(x='col1', y='col2') - x and y are REQUIRED (no aggregate_fn parameter exists)
- charts.number(expression='col', aggregate_fn='mean', title='Title') - all three REQUIRED
- charts.scatter() does NOT accept data_points parameter
- charts.line() does NOT accept aggregate_fn parameter

CORRECT EXAMPLES:
✓ charts.scatter(x='pickup_x', y='pickup_y', aggregate_col='fare', aggregate_fn='mean')
✓ charts.bar(x='passenger_count')
✓ charts.bar(x='trip_distance', data_points=50)
✓ charts.line(x='date', y='revenue')

INCORRECT EXAMPLES (THESE WILL FAIL):
✗ charts.bar('passenger_count') - missing parameter name 'x='
✗ charts.bar(column='passenger_count') - wrong parameter name, should be 'x='
✗ charts.scatter(x='lon', y='lat', data_points=50) - scatter doesn't have data_points
✗ charts.line(x='date', y='value', aggregate_fn='mean') - line doesn't have aggregate_fn

BEFORE CREATING EACH CHART:
- Verify the column exists in cux_df.data.columns
- Check column dtype to ensure it's appropriate for the chart type
- Use correct parameter names exactly as specified

Use layout: {kwargs.get('layout', 'feature_and_base')}
Use theme: {kwargs.get('theme', 'rapids_dark')}
Create {kwargs.get('num_charts', 3)} charts
Create {kwargs.get('num_widgets', 2)} widgets
""",
            
            "show_dashboard": """
Task: Display the dashboard

Steps:
1. Initialize results dictionary
2. Call d.app() to launch dashboard
3. Update results with success status
""",
            
            "export_dashboard": f"""
Task: Export dashboard to HTML file

Filepath: {kwargs.get('filepath', 'dashboard.html')}

Steps:
1. Initialize results dictionary
2. Ensure output directory exists
3. Call dashboard.export() which returns HTML content
4. Write HTML content to file
5. Store filepath in results
"""
        }
        
        instruction = task_instructions.get(task_name, f"Task: {task_name}\nNo specific instructions available.")
        
        # Construct prompt with API docs only
        prompt = f"""You are generating Python code for: {task_name}

Current State:
{state_info}

Task Instructions:
{instruction}

API Documentation:
{self.api_specs['cuxfilter_api']}

Code Requirements:
{self.api_specs['requirements']}

Generate ONLY executable Python code. No markdown, no explanations, no comments except essential ones.
Follow the API specification exactly. Do not invent methods or parameters that don't exist.
"""
        
        try:
            response = self.llm_client.chat([
                {
                    "role": "system", 
                    "content": "You are a Python code generator. Generate only valid, executable code based on provided API documentation. Follow specifications exactly. Never invent APIs."
                },
                {"role": "user", "content": prompt}
            ])
            
            code = response["choices"][0]["message"]["content"]
            
            # Clean up markdown if LLM added it
            code = re.sub(r'^```python\s*\n', '', code)
            code = re.sub(r'^```\s*\n', '', code)
            code = re.sub(r'\n```$', '', code)
            code = code.strip()
            
            # Safety check: ensure results is initialized
            if 'results' not in code or 'results = ' not in code:
                code = "results = {'success': False}\n\n" + code
            
            return code
            
        except Exception as e:
            return f"""# Error generating code: {str(e)}
results = {{'error': 'Code generation failed', 'message': '{str(e)}'}}
print('Error: ' + str(e))
"""
    
    def get_state_description(self, global_state: Dict[str, Any]) -> str:
        """Get description of current state."""
        state_desc = "Available variables:\n"
        
        if 'cux_df' in global_state:
            try:
                cux_df = global_state['cux_df']
                shape = cux_df.data.shape
                columns = list(cux_df.data.columns)
                dtypes = {col: str(dtype) for col, dtype in cux_df.data.dtypes.items()}
                state_desc += f"- cux_df (cuxfilter.DataFrame): shape={shape}, columns={columns}\n"
                state_desc += f"- Column types: {dtypes}\n"
            except:
                state_desc += "- cux_df (cuxfilter.DataFrame): exists but details unavailable\n"
        else:
            state_desc += "- cux_df: NOT AVAILABLE (must load data first)\n"
        
        if 'd' in global_state or 'dashboard' in global_state:
            state_desc += "- d or dashboard (cuxfilter.Dashboard): exists\n"
        else:
            state_desc += "- d or dashboard: NOT AVAILABLE (must create dashboard first)\n"
        
        return state_desc