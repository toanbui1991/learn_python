def test_string(some_string):
    """test for racecar is palisidrom

    Args:
        some_string (string): string
    """
    left_over = len(some_string) % 2
    if left_over == 0:
        return False
    else:
        #check for symetry
        mid_point = int(len(some_string)/2) - 1
        tests = []
        for i in range(mid_point):
            right = some_string[i]
            left = some_string[len(some_string) - 1]
            tests.append(right == left)
        return tests.all()