# buggy_1.py - Missing docstrings, bad variable names

def calc(l):
    t = 0
    for i in l:
        t = t + i
    return t

def avg(l):
    s = calc(l)
    n = len(l)
    return s / n

def mx(l):
    m = l[0]
    for x in l:
        if x > m:
            m = x
    return m

class Data:
    def __init__(self, v):
        self.v = v
    
    def p(self):
        print(self.v)
    
    def g(self):
        return self.v

if __name__ == "__main__":
    nums = [1, 2, 3, 4, 5]
    print(calc(nums))
    print(avg(nums))
    print(mx(nums))
    
    d = Data(42)
    d.p()