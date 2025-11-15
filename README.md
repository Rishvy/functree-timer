# Timeitt

A Python decorator for timing function calls and logging them in a hierarchical tree structure. Perfect for profiling and performance analysis of your Python applications.

## Features

- 🕐 **Automatic Timing**: Decorator-based timing for both sync and async functions
- 🌳 **Hierarchical Tree Structure**: Visualize function call relationships in a tree format
- 📊 **Configurable Logging**: Filter by minimum duration and top-k functions
- 🧵 **Thread-Safe**: Uses thread-local storage for multi-threaded applications
- 📝 **Detailed Logs**: Logs function names, durations, types (sync/async), and call depth

## Installation

```bash
pip install timeitt
```

## Quick Start

```python
from timeitt import timeit

@timeit(path="function_times.log", minimum_duration=0.05)
def my_function():
    # Your code here
    pass

@timeit()
async def my_async_function():
    # Your async code here
    pass
```

## Usage

### Basic Usage

```python
from timeitt import timeit

@timeit()
def calculate_sum(n):
    total = 0
    for i in range(n):
        total += i
    return total

result = calculate_sum(1000000)
```

### Custom Configuration

```python
@timeit(
    path="performance.log",      # Custom log file path
    minimum_duration=0.1,        # Only log functions taking >= 0.1 seconds
    top_k=10                     # Log only top 10 slowest functions
)
def slow_function():
    # Your code here
    pass
```

### Nested Function Calls

The decorator automatically tracks nested function calls and displays them in a tree structure:

```python
@timeit()
def outer_function():
    inner_function()
    another_inner_function()

@timeit()
def inner_function():
    time.sleep(0.1)

@timeit()
def another_inner_function():
    time.sleep(0.2)

outer_function()
```

This will generate a hierarchical tree in the log file showing the call relationships.

### Async Functions

```python
@timeit()
async def fetch_data():
    # Your async code
    await some_async_operation()
    return data
```

## Parameters

- `path` (str, default: "function_times.log"): Path to the log file where timing information will be written
- `minimum_duration` (float, default: 0.05): Minimum duration in seconds for a function call to be logged
- `top_k` (int or "full", default: "full"): Number of top functions to log, or "full" to log all functions
- `top_level_functions` (list, optional): List of top-level function names to track (currently not implemented)

## Output Format

The log file contains hierarchical tree structures showing function call relationships:

```
my_function (sync) took 0.1234 seconds
    ├── inner_function (sync) took 0.0500 seconds
    └── another_function (sync) took 0.0700 seconds
------
```

## Requirements

- Python 3.7+

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Your Name

