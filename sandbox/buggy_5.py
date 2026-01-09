# buggy_5.py - ALL PROBLEMS COMBINED!

import os
import sys
import random

def f(x, y):
    a = x
    b = y
    c = 0
    d = []
    temp = None
    unused = "never used"
    
    for i in range(len(a)):
        if i < len(b):
            c = a[i] + b[i]
            d.append(c)
    
    return d

def calc(nums):
    t = 0
    for n in nums:
        t = t + n
    return t / len(nums)

def process(data, m, opts):
    if m == "a":
        r = []
        for item in data:
            if item > 10:
                if opts["x"]:
                    if item % 2 == 0:
                        r.append(item * 2)
                    else:
                        if opts["y"]:
                            r.append(item * 3)
                        else:
                            r.append(item)
                else:
                    r.append(item + 1)
            else:
                if opts["z"]:
                    r.append(item)
        return r
    elif m == "b":
        s = 0
        for item in data:
            s = s + item
        return s / len(data)
    else:
        return None

def get_data(d, k, l, i):
    v1 = d[k]
    v2 = l[i]
    v3 = int(v1)
    return v3 + v2

def query_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query

class Thing:
    def __init__(self, x):
        self.x = x
        self.y = 0
        self.z = []
        self.unused_attr = "never used"
    
    def do(self, v):
        temp1 = v
        temp2 = 0
        unused_var = "not used"
        
        if v > 0:
            self.x = self.x + v
            return self.x
        else:
            return 0
    
    def calc(self):
        r = self.x / len(self.z)
        return r

def mega_process(input_data, config, flags, options, settings):
    result = {}
    temp_storage = []
    intermediate = []
    backup = []
    
    if config["mode"] == "full":
        for item in input_data:
            if item > config["threshold"]:
                if flags["process_high"]:
                    if item % 2 == 0:
                        temp_storage.append(item * settings["multiplier"])
                    else:
                        temp_storage.append(item + settings["offset"])
                else:
                    temp_storage.append(item)
        
        total = 0
        for val in temp_storage:
            total = total + val
        
        result["sum"] = total
        result["average"] = total / len(temp_storage)
        result["count"] = len(temp_storage)
        
        if options["include_stats"]:
            max_val = temp_storage[0]
            min_val = temp_storage[0]
            for val in temp_storage:
                if val > max_val:
                    max_val = val
                if val < min_val:
                    min_val = val
            result["max"] = max_val
            result["min"] = min_val
    
    return result

if __name__ == "__main__":
    l1 = [1, 2, 3]
    l2 = [4, 5, 6]
    print(f(l1, l2))
    
    nums = [10, 20, 30]
    print(calc(nums))
    print(calc([]))
    
    opts = {"x": True, "y": False, "z": True}
    print(process([5, 15, 25], "a", opts))
    
    print(query_user(1))