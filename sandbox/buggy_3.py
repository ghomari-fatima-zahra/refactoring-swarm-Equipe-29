# buggy_3.py - Functions too long, complex logic

def mega_function(data, mode, threshold, options):
    """
    This function does too many things.
    """
    if mode == "process":
        result = []
        for item in data:
            if item > threshold:
                if options.get("double"):
                    if item % 2 == 0:
                        result.append(item * 2)
                    else:
                        if options.get("triple"):
                            result.append(item * 3)
                        else:
                            result.append(item)
                else:
                    if item % 3 == 0:
                        result.append(item * 2)
                    else:
                        result.append(item + 1)
            else:
                if options.get("include_low"):
                    if item < 0:
                        result.append(0)
                    else:
                        result.append(item)
        return result
    elif mode == "analyze":
        total = 0
        count = 0
        max_val = data[0]
        min_val = data[0]
        for item in data:
            total += item
            count += 1
            if item > max_val:
                max_val = item
            if item < min_val:
                min_val = item
        avg = total / count
        if options.get("detailed"):
            return {
                "total": total,
                "count": count,
                "average": avg,
                "max": max_val,
                "min": min_val,
                "range": max_val - min_val
            }
        else:
            return avg
    elif mode == "filter":
        filtered = []
        for item in data:
            if options.get("even_only"):
                if item % 2 == 0:
                    if item > threshold:
                        filtered.append(item)
            elif options.get("odd_only"):
                if item % 2 != 0:
                    if item > threshold:
                        filtered.append(item)
            else:
                if item > threshold:
                    filtered.append(item)
        return filtered
    else:
        return None

def complex_calculator(x, y, z, operation, flags):
    """
    Complex calculator with nested conditions.
    """
    if operation == "add":
        if flags.get("multiply_first"):
            if flags.get("use_z"):
                return (x * y) + z
            else:
                return x * y
        else:
            if flags.get("use_z"):
                return x + y + z
            else:
                return x + y
    elif operation == "subtract":
        if flags.get("absolute"):
            if flags.get("use_z"):
                return abs(x - y - z)
            else:
                return abs(x - y)
        else:
            if flags.get("use_z"):
                return x - y - z
            else:
                return x - y
    elif operation == "multiply":
        if flags.get("square_result"):
            if flags.get("use_z"):
                result = x * y * z
                return result * result
            else:
                result = x * y
                return result * result
        else:
            if flags.get("use_z"):
                return x * y * z
            else:
                return x * y
    else:
        return 0

if __name__ == "__main__":
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    options = {"double": True, "include_low": False}
    print(mega_function(data, "process", 5, options))
    
    flags = {"multiply_first": True, "use_z": True}
    print(complex_calculator(2, 3, 4, "add", flags))