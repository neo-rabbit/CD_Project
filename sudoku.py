import time
import argparse
import itertools
import socket
from collections import deque

class Sudoku:
    def __init__(self, sudoku, base_delay=0.01, interval=10, threshold=5):
        self.grid = sudoku
        self.recent_requests = deque()
        self.base_delay = base_delay
        self.interval = interval
        self.threshold = threshold

    def _limit_calls(self, base_delay=0.01, interval=10, threshold=5):
        """Limit the number of requests made to the Sudoku object."""
        if base_delay is None:
            base_delay = self.base_delay
        if interval is None:
            interval = self.interval
        if threshold is None:
            threshold = self.threshold

        current_time = time.time()
        self.recent_requests.append(current_time)
        num_requests = len(
            [t for t in self.recent_requests if current_time - t < interval]
        )

        if num_requests > threshold:
            delay = base_delay * (num_requests - threshold + 1)
            time.sleep(delay)

    def __str__(self):
        string_representation = "| - - - - - - - - - - - |\n"

        for i in range(9):
            string_representation += "| "
            for j in range(9):
                string_representation += (
                    str(self.grid[i][j])
                    if self.grid[i][j] != 0
                    else f"\033[93m{self.grid[i][j]}\033[0m"
                )
                string_representation += " | " if j % 3 == 2 else " "

            if i % 3 == 2:
                string_representation += "\n| - - - - - - - - - - - |"
            string_representation += "\n"

        return string_representation

    def update_row(self, row, values):
        """Update the values of the given row."""
        self.grid[row] = values
    
    def update_column(self, col, values):
        """Update the values of the given column."""
        for row in range(9):
            self.grid[row][col] = values[row]

    def check_is_valid(
        self, row, col, num, base_delay=None, interval=None, threshold=None
    ):
        """Check if 'num' is not in the current row, column and 3x3 sub-box."""
        self._limit_calls(base_delay, interval, threshold)

        # Check if the number is in the given row or column
        for i in range(9):
            if self.grid[row][i] == num or self.grid[i][col] == num:
                return False

        # Check if the number is in the 3x3 sub-box
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                if self.grid[start_row + i][start_col + j] == num:
                    return False

        return True

    def check_row(self, row, base_delay=None, interval=None, threshold=None):
        """Check if the given row is correct."""
        self._limit_calls(base_delay, interval, threshold)

        # Check row
        if sum(self.grid[row]) != 45 or len(set(self.grid[row])) != 9:
            return False

        return True

    def check_column(self, col, base_delay=None, interval=None, threshold=None):
        """Check if the given row is correct."""
        self._limit_calls(base_delay, interval, threshold)

        # Check col
        if (
            sum([self.grid[row][col] for row in range(9)]) != 45
            or len(set([self.grid[row][col] for row in range(9)])) != 9
        ):
            return False

        return True

    def check_square(self, row, col, base_delay=None, interval=None, threshold=None):
        """Check if the given 3x3 square is correct."""
        self._limit_calls(base_delay, interval, threshold)

        # Check square
        if (
            sum([self.grid[row + i][col + j] for i in range(3) for j in range(3)]) != 45
            or len(
                set([self.grid[row + i][col + j] for i in range(3) for j in range(3)])
            )
            != 9
        ):
            return False

        return True

    def check(self, base_delay=None, interval=None, threshold=None):
        """Check if the given Sudoku solution is correct.

        You MUST incorporate this method without modifications into your final solution.
        """

        for row in range(9):
            if not self.check_row(row, base_delay, interval, threshold):
                return False

        # Check columns
        for col in range(9):
            if not self.check_column(col, base_delay, interval, threshold):
                return False

        # Check 3x3 squares
        for i in range(3):
            for j in range(3):
                if not self.check_square(i * 3, j * 3, base_delay, interval, threshold):
                    return False

        return True
    
    def generate_rows(self, row, base_delay=None, interval=None, threshold=None):
        incomplete_row = self.grid[row]
        rows1 = list(itertools.permutations([1,2,3,4,5,6,7,8,9]))
        rows2 = []
        for r in rows1:
            valid = True
            for i in range (9):
                if incomplete_row[i]!=0 and r[i]!=incomplete_row[i]:
                    valid = False
            if valid:
                self.update_row(row, r)
                if self.check_row(row, base_delay, interval, threshold):
                    rows2.append(r)
            self.update_row(row, incomplete_row)
        return rows2
    
    def get_valid_sections(self, section, rows1, rows2, rows3, base_delay=None, interval=None, threshold=None):
        pos = section*3
        valid_sections=[]
        for i in rows1:
            self.update_row(pos, i)
            for j in rows2:
                self.update_row(pos+1, j)
                for k in rows3:
                    self.update_row(pos+2, k)
                    if self.check_square(pos,0, base_delay, interval, threshold) and self.check_square(pos,3, base_delay, interval, threshold) and self.check_square(pos,6, base_delay, interval, threshold):
                        valid_sections.append([i,j,k])
        return valid_sections
    
    def get_it_solved(self, sections1, sections2, sections3, base_delay=None, interval=None, threshold=None):
        solutions = []
        for i in sections1:
            self.update_row(0, i[0])
            self.update_row(1, i[1])
            self.update_row(2, i[2])
            for j in sections2:
                self.update_row(3, j[0])
                self.update_row(4, j[1])
                self.update_row(5, j[2])
                for k in sections3:
                    self.update_row(6, k[0])
                    self.update_row(7, k[1])
                    self.update_row(8, k[2])
                    valid = True
                    for n in range (9):
                        if not self.check_column(n, base_delay, interval, threshold):
                            valid = False
                    if valid:
                        solutions.append([i[0],i[1],i[2],j[0],j[1],j[2],k[0],k[1],k[2]])
        return solutions

    def solve_work_pls(self, base_delay=None, interval=None, threshold=None):
        print("Processing row 1")
        rows1 = self.generate_rows(0, base_delay, interval, threshold)
        print("Processing row 2")
        rows2 = self.generate_rows(1, base_delay, interval, threshold)
        print("Processing row 3")
        rows3 = self.generate_rows(2, base_delay, interval, threshold)
        print("Processing row 4")
        rows4 = self.generate_rows(3, base_delay, interval, threshold)
        print("Processing row 5")
        rows5 = self.generate_rows(4, base_delay, interval, threshold)
        print("Processing row 6")
        rows6 = self.generate_rows(5, base_delay, interval, threshold)
        print("Processing row 7")
        rows7 = self.generate_rows(6, base_delay, interval, threshold)
        print("Processing row 8")
        rows8 = self.generate_rows(7, base_delay, interval, threshold)
        print("Processing row 9")
        rows9 = self.generate_rows(8, base_delay, interval, threshold)
        print("Processing section 1")
        sections1 = self.get_valid_sections(0, rows1, rows2, rows3, base_delay, interval, threshold)
        print("Processing section 2")
        sections2 = self.get_valid_sections(1, rows4, rows5, rows6, base_delay, interval, threshold)
        print("Processing section 3")
        sections3 = self.get_valid_sections(2, rows7, rows8, rows9, base_delay, interval, threshold)
        print("Processing solution")
        solution = self.get_it_solved(sections1, sections2, sections3, base_delay, interval, threshold)
        if len(solution)==1:
            return [list(solution[0][0]),
                    list(solution[0][1]),
                    list(solution[0][2]),
                    list(solution[0][3]),
                    list(solution[0][4]),
                    list(solution[0][5]),
                    list(solution[0][6]),
                    list(solution[0][7]),
                    list(solution[0][8])]
        else:
            print("ERROR: ", len(solution), " solutions found")
            return None

if __name__ == "__main__":

    parser=argparse.ArgumentParser()
    parser.add_argument('-p', type=int)
    parser.add_argument('-s', type=int)
    parser.add_argument('-a', type=str)
    args=parser.parse_args()
    httpport=args.p
    p2pport=args.s
    targetnode=args.a

    sudokuToSolve = Sudoku(
        [
            [2, 8, 0, 3, 4, 7, 9, 1, 0],
            [7, 5, 9, 0, 2, 0, 0, 3, 4], 
            [4, 0, 1, 5, 9, 8, 7, 2, 6], 
            [8, 6, 7, 9, 0, 3, 1, 0, 2], 
            [9, 0, 5, 7, 1, 2, 0, 0, 8], 
            [3, 1, 2, 0, 6, 4, 5, 9, 7], 
            [5, 0, 4, 1, 7, 6, 0, 8, 3], 
            [0, 0, 8, 2, 0, 9, 0, 5, 0], 
            [1, 2, 3, 4, 8, 0, 6, 7, 9]
        ]
    )
    print(sudokuToSolve)
    sudokuSolved = Sudoku(sudokuToSolve.solve_work_pls())
    print(sudokuSolved)
