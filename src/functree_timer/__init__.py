import time
import functools
import inspect
import os
import threading

_thread_local = threading.local()

# Shared default log file path - absolute path to root directory
_DEFAULT_LOG_PATH = os.path.abspath("function_times.log")


def _get_tracking_list():
    """Get or create the tracking list for current thread"""
    if not hasattr(_thread_local, 'tracking'):
        _thread_local.tracking = []
    return _thread_local.tracking

def _get_call_stack():
    """Get or create the call stack for current thread"""
    if not hasattr(_thread_local, 'call_stack'):
        _thread_local.call_stack = []
    return _thread_local.call_stack

def _get_next_call_id():
    """Get next unique call ID for current thread"""
    if not hasattr(_thread_local, 'call_id_counter'):
        _thread_local.call_id_counter = 0
    _thread_local.call_id_counter += 1
    return _thread_local.call_id_counter

def _build_call_tree(tracking):
    """Build a tree structure from flat tracking list"""
    tree = {}  
    root_nodes = []
    
    for entry in tracking:
        func_name, duration, func_type, depth, parent_id, call_id = entry
        if parent_id is None:
            root_nodes.append(entry)
        else:
            if parent_id not in tree:
                tree[parent_id] = []
            tree[parent_id].append(entry)
    
    for parent_id in tree:
        tree[parent_id].sort(key=lambda x: x[5])  
    
    return root_nodes, tree

def _format_tree_node(entry, tree, indent=0, prefix=""):
    func_name, duration, func_type, depth, parent_id, call_id = entry
    lines = []
    
    indent_str = "    " * indent
    node_str = f"{indent_str}{prefix}{func_name} ({func_type}) took {duration:.4f} seconds"
    lines.append(node_str)
    
    if call_id in tree:
        children = tree[call_id]
        for i, child in enumerate(children):
            is_last = (i == len(children) - 1)
            child_prefix = "└── " if is_last else "├── "
            child_lines = _format_tree_node(child, tree, indent + 1, child_prefix)
            lines.extend(child_lines)
    
    return lines

def _log_top_functions(logFile, top_k="full"):
    """Log functions in hierarchical tree structure"""
    tracking = _get_tracking_list()
    if not tracking:
        return
    
    root_nodes, tree = _build_call_tree(tracking)
    
    root_nodes.sort(key=lambda x: x[5])
    
    
    if top_k != "full" and top_k is not None:
        all_nodes = []
        def collect_nodes(entries):
            for entry in entries:
                all_nodes.append(entry)
                call_id = entry[5]
                if call_id in tree:
                    collect_nodes(tree[call_id])
        
        collect_nodes(root_nodes)
        all_nodes.sort(key=lambda x: x[1], reverse=True)
        top_nodes = all_nodes[:top_k]
        top_call_ids = {node[5] for node in top_nodes}
        
        def filter_tree(entries):
            filtered = []
            for entry in entries:
                call_id = entry[5]
                if call_id in top_call_ids:
                    filtered.append(entry)
                    if call_id in tree:
                        children = filter_tree(tree[call_id])
                        if children:
                            tree[call_id] = children
                elif call_id in tree:
                    children = filter_tree(tree[call_id])
                    if children:
                        filtered.append(entry)
                        tree[call_id] = children
            return filtered
        
        root_nodes = filter_tree(root_nodes)
    
    if root_nodes:
        log_dir = os.path.dirname(logFile)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        with open(logFile, "a", encoding="utf-8") as f:
            for root in root_nodes:
                lines = _format_tree_node(root, tree, indent=0, prefix="")
                for line in lines:
                    f.write(line + "\n")
            f.write("------\n")
    
    _thread_local.tracking = []
    _thread_local.call_stack = []

def timeit(path=None, minimum_duration=0.05, top_k="full", top_level_functions=None):
    """
    A decorator for timing function calls and logging them in a hierarchical tree structure.
    
    All decorators without a specified path will use the same shared log file by default.
    
    Args:
        path (str, optional): Path to the log file where timing information will be written.
                              If None, uses the shared default log file at root.
                              Defaults to None (shared log file).
        minimum_duration (float): Minimum duration in seconds for a function call to be logged.
                                 Defaults to 0.05 seconds.
        top_k (int or str): Number of top functions to log, or "full" to log all functions.
                           Defaults to "full".
        top_level_functions (list, optional): List of top-level function names to track.
                                            Currently not implemented.
    
    Returns:
        decorator: A decorator function that can be applied to any function.
    
    Example:
        @timeit(minimum_duration=0.1)  # Uses shared default log file
        def my_function():
            # Your code here
            pass
        
        @timeit(path="custom.log")  # Uses custom log file
        def another_function():
            # Your code here
            pass
    """
    
    # Use shared default path if not specified
    log_path = path if path is not None else _DEFAULT_LOG_PATH
    
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                call_stack = _get_call_stack()
                call_id = _get_next_call_id()
                
                parent_id = call_stack[-1][1] if call_stack else None
                depth = len(call_stack)
                
                call_stack.append((func.__name__, call_id))
                
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                finally:
                    call_stack.pop()
                
                duration = time.time() - start_time
                
                if duration >= minimum_duration:
                    tracking = _get_tracking_list()
                    tracking.append((func.__name__, duration, "async", depth, parent_id, call_id))
                    

                    if len(call_stack) == 0:
                        _log_top_functions(log_path, top_k)
                
                return result
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                call_stack = _get_call_stack()
                call_id = _get_next_call_id()
                
                parent_id = call_stack[-1][1] if call_stack else None
                depth = len(call_stack)
                
                call_stack.append((func.__name__, call_id))
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                finally:
                    call_stack.pop()
                
                duration = time.time() - start_time
                
                if duration >= minimum_duration:
                    tracking = _get_tracking_list()
                    tracking.append((func.__name__, duration, "sync", depth, parent_id, call_id))
                    
                 
                    if len(call_stack) == 0:
                        _log_top_functions(log_path, top_k)
                
                return result
            return sync_wrapper
    return decorator

__all__ = ['timeit']

