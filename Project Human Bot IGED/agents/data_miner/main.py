"""
DataMiner Agent for IGED
Data analysis and mining operations
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import csv

# Try to import data analysis libraries
try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    DATA_LIBS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Data analysis libraries not available: {e}")
    DATA_LIBS_AVAILABLE = False
    # Create dummy classes for type hints
    class pd:
        class DataFrame:
            pass
    class np:
        pass
    class plt:
        pass
    class sns:
        pass

logger = logging.getLogger(__name__)

class DataMinerAgent:
    def __init__(self, memory_engine):
        self.memory = memory_engine
        self.output_dir = Path("output/data_analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, target: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Execute data mining task"""
        try:
            logger.info(f"📊 DataMiner executing: {target}")
            
            # Check if data analysis libraries are available
            if not DATA_LIBS_AVAILABLE:
                return "❌ Data analysis libraries (pandas, numpy, matplotlib) not available. Please install: pip install pandas numpy matplotlib seaborn"
            
            if "analyze" in target.lower() or "analysis" in target.lower():
                return self._analyze_data(target)
            elif "extract" in target.lower() or "mine" in target.lower():
                return self._extract_data(target)
            elif "visualize" in target.lower() or "plot" in target.lower():
                return self._visualize_data(target)
            elif "statistics" in target.lower() or "stats" in target.lower():
                return self._generate_statistics(target)
            else:
                return self._general_data_processing(target)
                
        except Exception as e:
            logger.error(f"❌ DataMiner execution failed: {e}")
            return f"❌ Data mining error: {str(e)}"
    
    def _analyze_data(self, target: str) -> str:
        """Analyze data from file or source"""
        try:
            # Extract file path from target
            file_path = self._extract_file_path(target)
            if not file_path or not Path(file_path).exists():
                return "❌ No valid data file found. Please specify a file path."
            
            results = [f"📊 Data analysis for: {file_path}"]
            
            # Load data
            data = self._load_data(file_path)
            if data is None:
                return f"❌ Failed to load data from {file_path}"
            
            results.append(f"📈 Data shape: {data.shape}")
            results.append(f"📋 Columns: {list(data.columns)}")
            
            # Basic statistics
            results.append("\n📊 Basic Statistics:")
            stats = data.describe()
            results.append(str(stats))
            
            # Data types
            results.append(f"\n🔍 Data types:")
            for col, dtype in data.dtypes.items():
                results.append(f"  {col}: {dtype}")
            
            # Missing values
            missing = data.isnull().sum()
            if missing.sum() > 0:
                results.append(f"\n⚠️ Missing values:")
                for col, count in missing.items():
                    if count > 0:
                        results.append(f"  {col}: {count}")
            else:
                results.append("\n✅ No missing values found")
            
            # Save analysis report
            report_file = self.output_dir / f"analysis_report_{Path(file_path).stem}.txt"
            with open(report_file, "w") as f:
                f.write("\n".join(results))
            
            return f"✅ Data analysis complete. Report saved to {report_file}\n\n" + "\n".join(results)
            
        except Exception as e:
            logger.error(f"❌ Data analysis failed: {e}")
            return f"❌ Data analysis error: {str(e)}"
    
    def _extract_data(self, target: str) -> str:
        """Extract data from various sources"""
        try:
            results = [f"🔍 Data extraction for: {target}"]
            
            # Extract file path
            file_path = self._extract_file_path(target)
            if file_path and Path(file_path).exists():
                data = self._load_data(file_path)
                if data is not None:
                    # Extract sample
                    sample_size = min(100, len(data))
                    sample = data.head(sample_size)
                    
                    # Save extracted data
                    output_file = self.output_dir / f"extracted_data_{Path(file_path).stem}.csv"
                    sample.to_csv(output_file, index=False)
                    
                    results.append(f"✅ Extracted {sample_size} rows from {file_path}")
                    results.append(f"📁 Saved to: {output_file}")
                    
                    return "\n".join(results)
            
            return "❌ No valid data source found for extraction"
            
        except Exception as e:
            logger.error(f"❌ Data extraction failed: {e}")
            return f"❌ Data extraction error: {str(e)}"
    
    def _visualize_data(self, target: str) -> str:
        """Create data visualizations"""
        try:
            file_path = self._extract_file_path(target)
            if not file_path or not Path(file_path).exists():
                return "❌ No valid data file found for visualization"
            
            data = self._load_data(file_path)
            if data is None:
                return f"❌ Failed to load data from {file_path}"
            
            results = [f"📊 Creating visualizations for: {file_path}"]
            
            # Set up plotting style
            plt.style.use('default')
            sns.set_palette("husl")
            
            # Create multiple visualizations
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(f'Data Visualizations - {Path(file_path).stem}', fontsize=16)
            
            # 1. Histogram of numerical columns
            numerical_cols = data.select_dtypes(include=[np.number]).columns
            if len(numerical_cols) > 0:
                col = numerical_cols[0]
                axes[0, 0].hist(data[col].dropna(), bins=30, alpha=0.7, edgecolor='black')
                axes[0, 0].set_title(f'Histogram of {col}')
                axes[0, 0].set_xlabel(col)
                axes[0, 0].set_ylabel('Frequency')
            
            # 2. Box plot
            if len(numerical_cols) > 0:
                data[numerical_cols[:3]].boxplot(ax=axes[0, 1])
                axes[0, 1].set_title('Box Plot of Numerical Columns')
                axes[0, 1].tick_params(axis='x', rotation=45)
            
            # 3. Correlation heatmap
            if len(numerical_cols) > 1:
                corr_matrix = data[numerical_cols].corr()
                sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=axes[1, 0])
                axes[1, 0].set_title('Correlation Heatmap')
            
            # 4. Value counts for categorical columns
            categorical_cols = data.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                col = categorical_cols[0]
                value_counts = data[col].value_counts().head(10)
                value_counts.plot(kind='bar', ax=axes[1, 1])
                axes[1, 1].set_title(f'Top 10 Values in {col}')
                axes[1, 1].tick_params(axis='x', rotation=45)
            
            # Save plot
            plot_file = self.output_dir / f"visualizations_{Path(file_path).stem}.png"
            plt.tight_layout()
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            results.append(f"📈 Visualizations saved to: {plot_file}")
            
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"❌ Data visualization failed: {e}")
            return f"❌ Data visualization error: {str(e)}"
    
    def _generate_statistics(self, target: str) -> str:
        """Generate comprehensive statistics"""
        try:
            file_path = self._extract_file_path(target)
            if not file_path or not Path(file_path).exists():
                return "❌ No valid data file found for statistics"
            
            data = self._load_data(file_path)
            if data is None:
                return f"❌ Failed to load data from {file_path}"
            
            results = [f"📊 Statistical analysis for: {file_path}"]
            
            # Comprehensive statistics
            stats = {
                'shape': data.shape,
                'memory_usage': data.memory_usage(deep=True).sum(),
                'missing_values': data.isnull().sum().to_dict(),
                'data_types': data.dtypes.to_dict(),
                'numerical_stats': data.describe().to_dict() if len(data.select_dtypes(include=[np.number]).columns) > 0 else {},
                'categorical_stats': {}
            }
            
            # Categorical statistics
            categorical_cols = data.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                stats['categorical_stats'][col] = {
                    'unique_count': data[col].nunique(),
                    'most_common': data[col].mode().iloc[0] if len(data[col].mode()) > 0 else None,
                    'top_values': data[col].value_counts().head(5).to_dict()
                }
            
            results.append(f"📈 Dataset shape: {stats['shape']}")
            results.append(f"💾 Memory usage: {stats['memory_usage']} bytes")
            
            # Save detailed statistics
            stats_file = self.output_dir / f"statistics_{Path(file_path).stem}.json"
            with open(stats_file, "w") as f:
                json.dump(stats, f, indent=2, default=str)
            
            results.append(f"📁 Detailed statistics saved to: {stats_file}")
            
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"❌ Statistics generation failed: {e}")
            return f"❌ Statistics generation error: {str(e)}"
    
    def _general_data_processing(self, target: str) -> str:
        """General data processing tasks"""
        try:
            results = [f"🔧 General data processing for: {target}"]
            
            # Check for data files in current directory
            data_files = []
            for ext in ['.csv', '.xlsx', '.json', '.txt']:
                data_files.extend(Path('.').glob(f'*{ext}'))
            
            if data_files:
                results.append(f"📁 Found data files: {[f.name for f in data_files]}")
                
                # Process first file found
                file_path = data_files[0]
                data = self._load_data(str(file_path))
                
                if data is not None:
                    results.append(f"✅ Successfully loaded {file_path.name}")
                    results.append(f"📊 Shape: {data.shape}")
                    results.append(f"📋 Columns: {list(data.columns)}")
                else:
                    results.append(f"❌ Failed to load {file_path.name}")
            else:
                results.append("📁 No data files found in current directory")
            
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"❌ General data processing failed: {e}")
            return f"❌ General data processing error: {str(e)}"
    
    def _load_data(self, file_path: str) -> Optional[pd.DataFrame]:
        """Load data from various file formats"""
        try:
            path_obj = Path(file_path)
            
            if path_obj.suffix.lower() == '.csv':
                return pd.read_csv(path_obj)
            elif path_obj.suffix.lower() in ['.xlsx', '.xls']:
                return pd.read_excel(path_obj)
            elif path_obj.suffix.lower() == '.json':
                return pd.read_json(path_obj)
            elif path_obj.suffix.lower() == '.txt':
                # Try to read as CSV first, then as space-separated
                try:
                    return pd.read_csv(path_obj, sep=None, engine='python')
                except:
                    return pd.read_csv(path_obj, sep='\t')
            else:
                logger.warning(f"Unsupported file format: {path_obj.suffix}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load data from {file_path}: {e}")
            return None
    
    def _extract_file_path(self, text: str) -> Optional[str]:
        """Extract file path from command text"""
        import re
        
        # Look for file paths
        file_patterns = [
            r'["\']([^"\']*\.(?:csv|xlsx|xls|json|txt))["\']',
            r'([a-zA-Z0-9_\-\./\\]+\.(?:csv|xlsx|xls|json|txt))',
            r'(?:analyze|extract|process)\s+(?:the\s+)?([a-zA-Z0-9_\-\./\\]+\.(?:csv|xlsx|xls|json|txt))'
        ]
        
        for pattern in file_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'status': 'active',
            'agent': 'dataminer',
            'output_directory': str(self.output_dir),
            'capabilities': ['data_analysis', 'data_extraction', 'visualization', 'statistics']
        } 