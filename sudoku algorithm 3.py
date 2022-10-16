# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 19:14:02 2022

A sudoku solver. Does DFS but utilizes auto-filling from basic rules to 
speed up the search

@author: Mikkel Godsk Jørgensen
"""
from typing import *
import copy


class Sudoku:
    # Autofill modes
    _AUTOFILL_ROW, _AUTOFILL_COL, _AUTOFILL_BLOCK = 0,1,2
    
    def __init__(self, sudoku):
        self.plate = self.to_plate(sudoku)
        
    def __str__(self):
        sudoku = self.to_sudoku(self.plate)
        s = ""
        for i in range(9):
            for j in range(9):
                val = str(sudoku[i][j]) if sudoku[i][j]>0 else 'x'
                s += '{:s} '.format(val)
                if j%3==2:
                    s += ' '
            s += '\n'
            if i%3 == 2:
                s += '\n'
        return s
        
    def __getitem__(self, key: Tuple[int, int]):
        return self.plate[key[0]][key[1]]
    
    def __setitem__(self, key: Tuple[int, int], value: Set[int]):
        self.plate[key[0]][key[1]] = value
        assert self.is_consistent()
        
    def __eq__(self, other):
        for r in range(9):
            for c in range(9):
                if self[r,c] != other[r,c]:
                    return False
        return True
    
    @property
    def value_set(self):
        return set(range(1,10))
    
    def to_plate(self, sudoku):
        """
            Converts a sudoku array to a plate (of possibility sets)
        """
        plate = [[set() for i in range(9)] for j in range(9)]
        for i in range(9):
            for j in range(9):
                if sudoku[i][j] == None:  
                    # Empty cell
                    plate[i][j] = self.value_set
                else:  
                    # Filled cell
                    plate[i][j] = set([sudoku[i][j]])
        return plate


    def to_sudoku(self, plate):
        """
            Converts a plate (of possibility sets) into a sudoku array
        """
        sudoku = [[0 for i in range(9)] for j in range(9)]
        for i in range(9):
            for j in range(9):
                if len(plate[i][j]) == 1:
                    sudoku[i][j] = list(plate[i][j])[0]
        return sudoku
    
    def _focus_ix(self, entry, mode):
        """
            Gives a list of indices for a given row, column or block (the 
            "focus")
        """
        if mode == self._AUTOFILL_ROW: 
            return [(entry, c) for c in range(9)]
        elif mode == self._AUTOFILL_COL: 
            return [(r, entry) for r in range(9)]  # Get column list
        elif mode == self._AUTOFILL_BLOCK:
            return [(i,j) for i in range((entry//3)*3,(entry//3 + 1)*3) for j in range((entry%3)*3,(entry%3 + 1)*3)]
        
    def auto_fill(self):
        """
            Autofills using an algorithm where we loop through each row, 
            column and 3x3 block, and fill out a cell if there is only one 
            possible value for it based on possibility sets. The possibility 
            sets are shrinked based on:
                1. 'filled_values' being the numbers filled into other cells (if a number has been filled in, we shrink the possbility-set of the cell by it), and
                2. 'possibilities_others' being the union of possibilities of the other cells in the row/column/block (if a number cannot possibly be in the other cells, then it must belong to the current one!)
        """
        sets_reduced = 1
        while (not self.is_solved()) and (sets_reduced > 0):
            sets_reduced = 0
            for mode in [self._AUTOFILL_ROW, 
                         self._AUTOFILL_COL, 
                         self._AUTOFILL_BLOCK]:
                for entry in range(9):     # Entry is a row, col or block index
                    # Select focus
                    focus_ix = self._focus_ix(entry, mode)
                    focus = [self[ix] for ix in focus_ix]
                        
                    # Shrink possibility sets in "focus"
                    for current_cell in range(9):  # Cell index in row, col or block
                        if len(focus[current_cell]) == 1:  # Skip cell if filled
                            continue
                        filled_values = set()  # Cells filled in already in entry 
                        possibilities_others = set()  # Values that are possible for the other cells
                        for other_cell in range(9):
                            if current_cell == other_cell:
                                continue
                            
                            possibilities_others = possibilities_others.union(focus[other_cell])
                            
                            # Find filled elements
                            if len(focus[other_cell]) == 1:
                                filled_values = filled_values.union(focus[other_cell])
                                                    
                        # Adjust plate (shrinkage of sets)
                        prev_length = len(focus[current_cell])
                        focus[current_cell] = focus[current_cell].difference(filled_values)  # Remove values that are already filled in
                        curr_length = len(focus[current_cell])
                        if curr_length < prev_length:
                            sets_reduced += 1
                        if len(possibilities_others) == 8:
                            focus[current_cell] = self.value_set.difference(possibilities_others)  # If a value cannot be elsewhere in the entry, fill it in
                        
                    # Update plate
                    for i, ix in enumerate(focus_ix):
                        r, c = ix
                        self.plate[r][c] = focus[i]
                        
        return self
        
    def is_solved(self):
        """
            Checks if the sudoku is solved 
            (consistently and completely filled in)
        """
        return self.is_filled() and self.is_consistent()
        
    def is_consistent(self):
        """
            Checks if the filled-in values are consistent 
            (i.e. singleton possibility sets)
        """
        for mode in [self._AUTOFILL_ROW, 
                     self._AUTOFILL_COL, 
                     self._AUTOFILL_BLOCK]:
            for entry in range(9):
                focus_ix = self._focus_ix(entry, mode)
                focus = [self[ix] for ix in focus_ix]
                singletons = [c for c in focus if len(c)==1]
                if len(set().union(*singletons)) < len(singletons):
                    return False
        return True
    
    def is_filled(self):
        """
            Checks if all possibility sets are singletons
        """
        for i in range(9):
            for j in range(9):
                if len(self[i,j]) > 1:
                    return False
        return True
    
    def is_viable(self):
        """
            Checks for empty possibility sets
        """
        for i in range(9):
            for j in range(9):
                if len(self[i,j]) == 0:
                    return False
        return True
    

def DFS_solve(sudoku: Sudoku):
    """
        Agent algorithm loop (DFS):
            Autofill plate.
            Check if solved.
            Get actions.
            Perform action.
            Repeat.
    """
    sudoku.auto_fill()
    if (not sudoku.is_viable()) or (not sudoku.is_consistent()):
        return None
    elif sudoku.is_solved():
        return sudoku
    
    for r in range(9):
        for c in range(9):
            if len(sudoku[r, c]) == 1:  # Skip cells already filled out
                continue
            
            for v in sudoku[r, c]:  # Go through all possibilities
                sudoku_copy = copy.deepcopy(sudoku)
                
                # We try inserting a value and solve from here
                sudoku_copy[r, c] = set([v])
                solution = DFS_solve(sudoku_copy)
                
                # If the attempt resulted in the solution, we return it
                if solution is not None:
                    return solution
                
    # If no attempts resulted in a solution, we return None
    return None


if __name__ == '__main__':
    x = None
    """sudoku = Sudoku([
        [2,6,x, 3,x,x, x,1,x],
        [5,8,x, 4,x,x, 7,x,x],
        [x,x,x, x,6,x, x,2,8],
        
        [x,x,x, 8,3,x, x,x,7],
        [x,1,2, 7,x,5, 3,x,x],
        [x,5,x, x,x,x, x,x,x],
        
        [x,4,6, x,x,x, x,x,1],
        [7,x,x, x,x,x, x,4,x],
        [x,3,5, x,x,x, 6,x,x],    
    ])
    solution = Sudoku([
        [2,6,9, 3,7,8, 4,1,5],
        [5,8,1, 4,2,9, 7,6,3],
        [4,7,3, 5,6,1, 9,2,8],
        
        [6,9,4, 8,3,2, 1,5,7],
        [8,1,2, 7,4,5, 3,9,6],
        [3,5,7, 1,9,6, 2,8,4],
        
        [9,4,6, 2,5,7, 8,3,1],
        [7,2,8, 6,1,3, 5,4,9],
        [1,3,5, 9,8,4, 6,7,2],
    ])"""
    sudoku = Sudoku([
        [7,x,x, x,x,x, x,x,3],
        [x,x,6, x,7,x, x,1,x],
        [x,5,1, x,x,4, 7,x,x],
        
        [x,x,x, x,x,5, 2,x,x],
        [x,4,x, x,1,x, x,8,x],
        [x,x,5, 8,x,x, x,x,x],
        
        [x,x,8, 6,x,x, 5,9,x],
        [x,2,x ,x,9,x, 4,x,x],
        [4,x,x ,x,x,x, x,x,1],
    ])
    solution = Sudoku([
        [7,8,4, 1,2,6, 9,5,3],
        [2,3,6, 5,7,9, 8,1,4],
        [9,5,1, 3,8,4, 7,2,6],
        
        [8,1,7, 4,6,5, 2,3,9],
        [3,4,2, 9,1,7, 6,8,5],
        [6,9,5, 8,3,2, 1,4,7],
        
        [1,7,8 ,6,4,3, 5,9,2],
        [5,2,3 ,7,9,1, 4,6,8],
        [4,6,9 ,2,5,8, 3,7,1],
    ])
    
    solved = DFS_solve(sudoku)
    print(solved)
    assert solved == solution