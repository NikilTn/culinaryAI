"""
State manager module to track global application state.
This module provides shared state objects that can be imported by different parts of the application.
"""

# Dictionary to track active recipe generation tasks by user_id
active_generation_tasks = {} 