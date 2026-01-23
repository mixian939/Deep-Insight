# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a quantitative investment platform based on Microsoft's Qlib. It provides a comprehensive AI-oriented platform for quantitative research, including data processing, model training, backtesting, and strategy execution.

The project structure:
- `main.py` - Simple entry point (hello world script)
- `qlib/` - Main package containing the full Qlib library
  - `qlib/qlib/` - The actual qlib Python package
  - `qlib/examples/` - Extensive examples and benchmarks
  - `qlib/scripts/` - Utility scripts including data download
  - `qlib/tests/` - Test suite

## Common Commands

### Development Setup
```bash
# Install with dependencies
pip install -e .[dev]

# Install all optional dependencies
pip install -e .[pywinpty,dev,lint,docs,package,test,analysis,rl]
```

### Building Cython Extensions (Required)
The package includes Cython modules that must be compiled before use:
```bash
# Build prerequisite C++ extensions
make prerequisite

# Or manually:
pip install --upgrade setuptools wheel cython numpy
python -c "from setuptools import setup, Extension; from Cython.Build import cythonize; import numpy; extensions = [Extension('qlib.data._libs.rolling', ['qlib/data/_libs/rolling.pyx'], language='c++', include_dirs=[numpy.get_include()]), Extension('qlib.data._libs.expanding', ['qlib/data/_libs/expanding.pyx'], language='c++', include_dirs=[numpy.get_include()])]; setup(ext_modules=cythonize(extensions, language_level='3'), script_args=['build_ext', '--inplace'])"
```

### Data Preparation
```bash
# Download CN market data (daily)
python -m qlib.cli.data qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn

# Download CN market data (1-minute high-frequency)
python -m qlib.cli.data qlib_data --target_dir ~/.qlib/qlib_data/cn_data_1min --region cn --interval 1min

# Download US market data
python -m qlib.cli.data qlib_data --target_dir ~/.qlib/qlib_data/us_data --region us
```

### Running Workflows
```bash
# Run a workflow from YAML config (recommended to run from examples directory)
cd examples
qrun benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml

# Or using Python module directly
python -m qlib.cli.run examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml
```

### Testing
```bash
# Install test dependencies
make test

# Run pytest
pytest

# Run specific test
pytest tests/data_mid_layer_tests/test_handler.py

# Skip slow tests
pytest -m "not slow"
```

### Linting
```bash
# Run all linters
make lint

# Individual linters
make black      # Check code formatting
make pylint     # Static analysis
make flake8     # Style checking
make mypy       # Type checking
```

## Architecture

### Core Components

**Data Layer** (`qlib/data/`)
- Provider pattern for data sources (local, NFS, server)
- Expression engine for feature computation
- Dataset and handler abstraction for ML pipelines
- Caching mechanisms (ExpressionCache, DatasetCache)

**Backtest Engine** (`qlib/backtest/`)
- SimulatorExecutor for order execution simulation
- Account and position management
- Exchange simulation with slippage and transaction costs
- Profit attribution and reporting

**Workflow Management** (`qlib/workflow/`)
- Experiment tracking (alternative to MLflow with richer interface)
- Recorder API for logging experiments
- Configuration-driven and code-based workflows

**Model Framework** (`qlib/model/`)
- Abstract base classes for forecast models
- Ensemble and meta-learning support
- Integration with various ML frameworks

**Strategy Module** (`qlib/strategy/`)
- Signal-based portfolio strategies
- TopkDropoutStrategy and other standard strategies
- Strategy composition and nesting support

### Key Design Patterns

1. **Initialization**: `qlib.init()` sets up configuration, mounts data, and initializes components
   - Two modes: `client` (default) and `server`
   - Supports YAML config files with `init_from_yaml_conf()`
   - Auto-discovery of project config with `auto_init()`

2. **Two Interface Styles**:
   - **Config-based**: Use YAML files with `qrun workflow.yaml`
   - **Code-based**: Use `init_instance_by_config()` to instantiate components programmatically

3. **Configuration System** (`qlib/config.py`):
   - Central config object `C` (Pydantic-based)
   - Provider URI management for different frequencies
   - Component registration and discovery

4. **Experiment Recording** (`qlib/workflow/`):
   - `R` global recorder for experiment tracking
   - Records predictions, portfolios, and analysis results
   - Supports multiple backends (MLflow by default)

### Common Workflow Pattern

```python
import qlib
from qlib.constant import REG_CN
from qlib.utils import init_instance_by_config
from qlib.workflow import R

# Initialize
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region=REG_CN)

# Load config
model = init_instance_by_config(config["model"])
dataset = init_instance_by_config(config["dataset"])

# Start experiment
with R.start(experiment_name="my_exp"):
    # Train
    model.fit(dataset)

    # Record results
    recorder = R.get_recorder()
    recorder.save_objects(model=model)
```

## Important Notes

- **Python Version**: Requires Python 3.8+ (project specifies >=3.10)
- **Cython Dependencies**: Must compile `.pyx` files before first use
- **Data Mounting**: Qlib can mount NFS shares automatically or use local paths
- **Multi-frequency**: Supports multiple data frequencies (day, 1min, etc.) simultaneously
- **Region Support**: Different markets (CN, US) have different configurations
- **Windows Note**: On Windows, use `make prerequisite` which handles platform-specific dependencies

## File Locations

- Main package: `qlib/qlib/`
- Examples: `qlib/examples/` (includes benchmarks, tutorials, workflow examples)
- Scripts: `qlib/scripts/` (data download, utilities)
- Tests: `qlib/tests/`
- Documentation: `qlib/docs/`
- CLI entry points: `qlib/qlib/cli/` (run.py, data.py)
