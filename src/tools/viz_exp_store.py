# src/tools/viz_exp_store.py - Simplified storage for visualization experiments
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

class VizExperimentStore:
    """Simple storage for visualization experiment results."""
    
    def __init__(self, runs_file="runs/viz_experiments.jsonl"):
        self.runs_file = Path(runs_file)
        
        # Create the directory if it doesn't exist
        self.runs_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create the file if it doesn't exist
        if not self.runs_file.exists():
            self.runs_file.touch()
    
    def clear_all(self):
        """Delete all stored experiments."""
        self.runs_file.write_text("", encoding="utf-8")
    
    def save_experiment(self, experiment_data: Dict):
        """Save a visualization experiment result."""
        # Add timestamp
        experiment_data["timestamp"] = time.time()
        experiment_data["date"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert to JSON-serializable format
        def make_serializable(obj):
            """Recursively convert non-serializable objects to strings."""
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif hasattr(obj, 'dtype'):  # numpy/pandas types
                return str(obj)
            elif hasattr(obj, 'isoformat'):  # datetime types
                return obj.isoformat()
            else:
                try:
                    json.dumps(obj)
                    return obj
                except (TypeError, ValueError):
                    return str(obj)
        
        experiment_data = make_serializable(experiment_data)
        
        # Append to file
        with self.runs_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(experiment_data) + "\n")
    
    def load_all_experiments(self) -> List[Dict]:
        """Load all saved visualization experiments."""
        experiments = []
        
        if not self.runs_file.exists():
            return experiments
        
        with self.runs_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    try:
                        experiment = json.loads(line)
                        experiments.append(experiment)
                    except json.JSONDecodeError:
                        # Skip corrupted lines
                        continue
        
        return experiments
    
    def find_best_dashboard(self, metric_name: str = "interactivity") -> Optional[Dict]:
        """Find the best dashboard based on a given metric."""
        experiments = self.load_all_experiments()
        
        if not experiments:
            return None
        
        best_experiment = None
        best_score = None
        
        # For visualizations, we might score based on number of charts, interactivity, etc.
        for experiment in experiments:
            results = experiment.get('results', {})
            
            # Calculate a score based on the metric
            if metric_name == "interactivity":
                score = results.get('num_filters', 0) + results.get('num_charts', 0) * 0.5
            elif metric_name == "completeness":
                score = results.get('num_charts', 0)
            else:
                score = results.get(metric_name, 0)
            
            if score is None:
                continue
            
            if best_experiment is None or score > best_score:
                best_experiment = experiment
                best_score = score
        
        return best_experiment
    
    def get_recent_experiments(self, limit: int = 10) -> List[Dict]:
        """Get the most recent visualization experiments."""
        experiments = self.load_all_experiments()
        
        # Sort by timestamp (most recent first)
        experiments.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return experiments[:limit]
    
    def count_experiments(self) -> int:
        """Count total number of visualization experiments."""
        return len(self.load_all_experiments())
    
    def get_dashboards_by_data_source(self, data_path: str) -> List[Dict]:
        """Get all dashboards created for a specific data source."""
        experiments = self.load_all_experiments()
        
        matching = []
        for exp in experiments:
            params = exp.get('parameters', {})
            if params.get('path') == data_path:
                matching.append(exp)
        
        return matching
    
    def get_chart_usage_stats(self) -> Dict[str, int]:
        """Get statistics on which chart types are used most."""
        experiments = self.load_all_experiments()
        
        chart_counts = {}
        for exp in experiments:
            results = exp.get('results', {})
            charts = results.get('charts', [])
            
            for chart in charts:
                chart_type = chart.get('type', 'unknown')
                chart_counts[chart_type] = chart_counts.get(chart_type, 0) + 1
        
        return chart_counts
    
    def get_layout_usage_stats(self) -> Dict[str, int]:
        """Get statistics on which layouts are used most."""
        experiments = self.load_all_experiments()
        
        layout_counts = {}
        for exp in experiments:
            results = exp.get('results', {})
            layout = results.get('layout', 'unknown')
            layout_counts[layout] = layout_counts.get(layout, 0) + 1
        
        return layout_counts
    
    def get_theme_usage_stats(self) -> Dict[str, int]:
        """Get statistics on which themes are used most."""
        experiments = self.load_all_experiments()
        
        theme_counts = {}
        for exp in experiments:
            results = exp.get('results', {})
            theme = results.get('theme', 'unknown')
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        return theme_counts
    
    def get_experiment_summary(self) -> Dict:
        """Get a comprehensive summary of all experiments."""
        experiments = self.load_all_experiments()
        
        if not experiments:
            return {
                'total_experiments': 0,
                'successful_experiments': 0,
                'failed_experiments': 0,
                'chart_usage': {},
                'layout_usage': {},
                'theme_usage': {}
            }
        
        successful = sum(1 for exp in experiments if exp.get('success', False))
        failed = len(experiments) - successful
        
        return {
            'total_experiments': len(experiments),
            'successful_experiments': successful,
            'failed_experiments': failed,
            'success_rate': f"{(successful/len(experiments)*100):.1f}%",
            'chart_usage': self.get_chart_usage_stats(),
            'layout_usage': self.get_layout_usage_stats(),
            'theme_usage': self.get_theme_usage_stats()
        }
    
    def export_experiments_to_json(self, filepath: str):
        """Export all experiments to a JSON file."""
        experiments = self.load_all_experiments()
        
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(experiments, f, indent=2)
    
    def search_experiments(self, keyword: str) -> List[Dict]:
        """Search experiments by keyword in task or parameters."""
        experiments = self.load_all_experiments()
        
        matching = []
        keyword_lower = keyword.lower()
        
        for exp in experiments:
            task = exp.get('task', '').lower()
            params = str(exp.get('parameters', {})).lower()
            
            if keyword_lower in task or keyword_lower in params:
                matching.append(exp)
        
        return matching