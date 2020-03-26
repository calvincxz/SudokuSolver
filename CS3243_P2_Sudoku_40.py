import sys
import copy
import math
import time
import itertools
from collections import deque

# Running script: given code can be run with the command:
# python file.py, ./path/to/init_state.txt ./output/output.txt

class Sudoku(object):
    def __init__(self, puzzle):
        # you may add more attributes if you need
        self.puzzle = puzzle # self.puzzle is a list of lists
        self.ans = copy.deepcopy(puzzle) # self.ans is a list of lists
        self.domain = self.init_domain() # only called once during initialization
        self.nodes = 0
        self.arcs = self.init_arcs()

    def init_domain(self):
        domain = {}
        for i in range(81):
            domain[i] = set([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for row in range(9):
            for col in range(9):
                # store domain of variables with keys from 0 to 80.
                index = row * 9 + col
                value = puzzle[row][col]
                if value != 0:
                    domain = self.remove_values(row, col, value, domain) 
        return domain

    # Gets list of index for cells in same row, column and block for a given row, col.
    def get_list_of_indices(self, row, col): 
        indices = list()
        for i in range(9):
            if i != col:
                indices.append(row * 9 + i)

        for i in range(9):
            if i != row:
                indices.append(col + 9 * i)

        block_row = math.floor(row / 3)
        block_col = math.floor(col / 3)
        for i in range(3):
            for j in range(3):
                index = int((block_row * 3 + i) * 9 + block_col * 3 + j)
                if (index != row * 9 + col) and (index//9 != row) and (index%9 != col):
                    indices.append(index)
        return indices   

    # Removes the specified value from constrained squares and returns the new dictionary
    def remove_values(self, row, col, value, remaining_values):
        remaining_values[row * 9 + col] = { value }

        for index in self.get_list_of_indices(row, col):
            remaining_values[index].discard(value)

        return remaining_values

    # return the list of empty squares
    def get_empty_squares(self):
        empty_squares = []
        for row in range(9):
            for col in range(9):
                if puzzle[row][col] == 0:
                    empty_squares.append([row, col]) 
        return empty_squares

    # returns the row, col of the most contrained empty square (MRV heuristic)
    # returns None if all squares are filled
    def get_most_constrained_square(self):
        result = None
        min_size = 10
        for row in range(9):
            for col in range(9):
                # ignore non-empty cells
                if puzzle[row][col] != 0:
                    continue

                index = row * 9 + col
                size = len(self.domain[index])  

                # optimize return since size of 1 is already the best result
                if size == 1:
                    return row, col

                # find the square with domain of min. size
                if size < min_size:
                    min_size = size
                    result = row, col

        return result

    # Degree Heuristic
    # Returns the next variable to be assigned a value will be the variable which 
    # is involved in the most number of constraints with other unassigned variables.
    def get_most_constraining_square(self):
        max_size = -1

        result = None
        for i in range(9):
            for j in range(9):
                if puzzle[i][j] != 0:
                    continue

                count = 0
                indices = self.get_list_of_indices(i, j)
                for index in indices:
                    if puzzle[index//9][index%9] == 0:
                        count+=1

                if count > max_size:
                    max_size = count
                    result = i, j
        return result


    def solve_backtrack(self):    
        # MRV heuristic
        selected_square = self.get_most_constrained_square()
        #selected_square = self.get_most_constraining_square()
        #print(selected_square)
        if selected_square == None: 
            return True
        
        row = selected_square[0]
        col = selected_square[1]
        values = self.domain[row * 9 + col]
        indices = self.get_list_of_indices(row, col)
        
        while len(values) != 0: 
            # select random variable
            # value = values.pop()  

            # select the least constraining value 
            value = self.get_least_constraining_value(values, indices)
            values.discard(value)

            # forward check for null domains    
            #if self.forward_check(value,indices): #Switch comment to disable/enable ac3
            if self.is_consistent_assignment(value, indices):
                puzzle[row][col] = value
                temp = copy.deepcopy(self.domain)
                self.domain = self.remove_values(row, col, value, self.domain)
                self.nodes += 1

                if self.AC3(): #Change to true to disable ac3
                #if True:

                    if self.solve_backtrack():
                        return True
        
            puzzle[row][col] = 0
            self.domain = temp
                
        return False

    # check cells in same row, col and block, returns the value which affects the least cells
    # UNUSED HEURISTIC
    def get_least_constraining_value(self, values, indices):
        result = None
        min_constraints = 1000
        #min_constraints = -1
        for value in values:
            num_of_constraints = 0
            for index in indices:
                if value in self.domain[index]: # TODO: Check if this is doing the opposite (unexpected result of being faster/slower)
                    num_of_constraints += 1

            # update min
            if min_constraints > num_of_constraints:
            #if min_constraints < num_of_constraints:
                min_constraints = num_of_constraints
                result = value

        return result

    # Checks if setting a value in a cell causes domain size of relevant cells to become 0
    def forward_check(self, value, indices): 
        for index in indices:
            domain = self.domain[index]
            if len(domain) == 1 and value in domain:
                return False
                                                 
        return True

    # Check assignment consistency
    def is_consistent_assignment(self, value, indices):
        for index in indices:
            if puzzle[index//9][index%9] == value:
                return False
        return True

    # Initialize all arcs in constraint graph 
    def init_arcs(self):
        arcs = list()
        for i in range(81):
            for j in range(81):
                ipos = (i//9, i%9)
                jpos = (j//9, j%9)

                if ipos == jpos:
                    continue
                if ipos[0] == jpos[0]:
                    arcs.append((i,j))
                    continue
                if ipos[1] == jpos[1]:
                    arcs.append((i,j))
                    continue

                if (ipos[0]//3 == jpos[0]//3) and (ipos[1]//3 == jpos[1]//3):
                    arcs.append((i,j))
        return arcs


    # AC3 Inference Mechanism
    # Returns false if inconsistency is found and true otherwise
    def AC3(self):
        # Initialize queue of all arcs
        queue = deque(self.arcs)

        while queue:
            edge = queue.popleft()
            #print(edge)
            if self.revise(edge):
                if len(self.domain[edge[0]]) == 0:
                    #print("AC3 fail")
                    return False

                    for k in get_list_of_indices(edge[0]//9, edge[0]%9):
                        if k == edge[1]:
                            continue
                        queue.append((k,edge[0]))

        return True

    # Revise Edge
    # Returns true if param domain is revised
    def revise(self, edge):
        revised = False
        temp = set(self.domain[edge[0]])
        #print("Parent " + str(edge[0])+" : " + str(self.domain[edge[0]]) + " Child " + str(edge[1])+" : " + str(self.domain[edge[1]]))
        for x in self.domain[edge[0]]:
            hasSatisfyingChildValue = False
            for y in self.domain[edge[1]]:
                if x != y: # if there is at least 1 satisfiable value in Xj
                    hasSatisfyingChildValue = True
                    break
            if hasSatisfyingChildValue:
                continue
    
            #print("Parent " + str(edge[0])+" : " + str(self.domain[edge[0]]) + " Child " + str(edge[1])+" : " + str(self.domain[edge[1]]))
            #print("Removed : "+str(x))
            temp.remove(x)
            revised = True
        if revised:
            self.domain[edge[0]] = temp
            #print("Parent " + str(edge[0])+" : " + str(self.domain[edge[0]]) + " Child " + str(edge[1])+" : " + str(self.domain[edge[1]]), end="\n\n")


        #print("Parent " + str(edge[0])+" : " + str(self.domain[edge[0]]) + " Child " + str(edge[1])+" : " + str(self.domain[edge[1]]), end="\n\n")

        return revised
    
    def solve(self):
        start = time.time()
        if self.solve_backtrack():
            print(self.puzzle)
        else:
            print("UNSOLVABLE")

        end = time.time()
        print("nodes generated: ", self.nodes)
        print("duration: ", end - start)
        # self.ans is a list of lists
        return self.puzzle

    # you may add more classes/functions if you think is useful
    # However, ensure all the classes/functions are in this file ONLY
    # Note that our evaluation scripts only call the solve method.
    # Any other methods that you write should be used within the solve() method.

if __name__ == "__main__":
    # STRICTLY do NOT modify the code in the main function here
    if len(sys.argv) != 3:
        print ("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise ValueError("Wrong number of arguments!")

    try:
        f = open(sys.argv[1], 'r')
    except IOError:
        print ("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise IOError("Input file not found!")

    puzzle = [[0 for i in range(9)] for j in range(9)]
    lines = f.readlines()

    i, j = 0, 0
    for line in lines:
        for number in line:
            if '0' <= number <= '9':
                puzzle[i][j] = int(number)
                j += 1
                if j == 9:
                    i += 1
                    j = 0

    sudoku = Sudoku(puzzle)
    ans = sudoku.solve()

    with open(sys.argv[2], 'a') as f:
        for i in range(9):
            for j in range(9):
                f.write(str(ans[i][j]) + " ")
            f.write("\n")
