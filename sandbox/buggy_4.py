# buggy_4.py - Missing error handling

def divide_numbers(a, b):
    """Divide two numbers."""
    return a / b

def get_item_from_list(items, index):
    """Get item at index."""
    return items[index]

def read_file_content(filename):
    """Read file content."""
    file = open(filename, 'r')
    content = file.read()
    file.close()
    return content

def parse_integer(value):
    """Parse string to integer."""
    return int(value)

def access_dictionary(data, key):
    """Access dictionary value."""
    return data[key]

def calculate_average(numbers):
    """Calculate average of numbers."""
    total = sum(numbers)
    count = len(numbers)
    return total / count

def connect_to_database(host, port):
    """Connect to database."""
    connection = f"Connected to {host}:{port}"
    return connection

def process_user_input(user_data):
    """Process user input without validation."""
    name = user_data["name"]
    age = int(user_data["age"])
    email = user_data["email"]
    
    result = {
        "name": name.upper(),
        "age": age + 1,
        "email": email.lower()
    }
    
    return result

class FileProcessor:
    def __init__(self, filename):
        self.filename = filename
        self.data = None
    
    def load_data(self):
        """Load data from file."""
        with open(self.filename, 'r') as f:
            self.data = f.read()
    
    def parse_data(self):
        """Parse data as JSON."""
        import json
        return json.loads(self.data)
    
    def get_value(self, key):
        """Get value from parsed data."""
        parsed = self.parse_data()
        return parsed[key]

if __name__ == "__main__":
    print(divide_numbers(10, 2))
    print(divide_numbers(10, 0))
    
    items = [1, 2, 3]
    print(get_item_from_list(items, 1))
    print(get_item_from_list(items, 10))
    
    print(parse_integer("123"))
    print(parse_integer("abc"))