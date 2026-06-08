def mono_convex(grid, k, c):
    '''
    Returns True if all tests are passed, False otherwise.
    '''
    grid.append((k, c)) # add current pair
    grid.sort(key = lambda pair: pair[0]) # sort by strike

    # position of new pair post sort
    curr_idx = next(i for i, pair in enumerate(grid) if pair == (k, c))
    
    def get_k(idx):
        return grid[idx][0]
    
    def get_c(idx):
        return grid[idx][1]
    
    if len(grid) >= 2:
        if get_c(curr_idx) >= get_c(curr_idx - 1):
            grid.remove((k, c)) # remove most recent pair
            return False
    
    if len(grid) >= 3:
        # spreads
        dc1 = get_c(curr_idx-2) - get_c(curr_idx-1)
        dc2 = get_c(curr_idx-1) - get_c(curr_idx)
        dk1 = get_k(curr_idx-1) - get_k(curr_idx-2)
        dk2 = get_k(curr_idx) - get_k(curr_idx-1)

        # normalised spreads
        norm_spread1 = dc1 / dk1 # slope of first segment
        norm_spread2 = dc2 / dk2 # slope of second segment

        # check convexity with some tolerance, slopes should decrease smoothly
        if norm_spread2 > norm_spread1 * 1.1: 
            grid.remove((k, c)) # remove most recent pair
            return False
        
    grid.remove((k, c)) # remove most recent pair
    return True

