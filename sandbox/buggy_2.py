# buggy_2.py - Unused variables, no type hints

import os
import sys
import random

def process_data(data):
    """Process some data."""
    result = []
    temp = 0
    unused_var = "never used"
    counter = 0
    
    for item in data:
        if item > 0:
            result.append(item * 2)
            counter += 1
    
    extra_var = "also not used"
    
    return result

def calculate_sum(numbers):
    """Calculate sum with unused variables."""
    total = 0
    max_value = 0
    min_value = 0
    average = 0
    
    for num in numbers:
        total += num
    
    return total

def filter_data(items):
    """Filter data without type hints."""
    filtered = []
    temp_list = []
    backup = []
    
    for item in items:
        if item % 2 == 0:
            filtered.append(item)
    
    return filtered

class DataProcessor:
    def __init__(self, data):
        self.data = data
        self.unused_attribute = "never accessed"
        self.temp = []
    
    def process(self):
        """Process data with unused variables."""
        result = []
        temp_var = 0
        
        for item in self.data:
            result.append(item)
        
        return result

if __name__ == "__main__":
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print(process_data(numbers))
    print(calculate_sum(numbers))
    print(filter_data(numbers))