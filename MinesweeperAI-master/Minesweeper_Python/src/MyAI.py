# ==============================CS-199==================================
# FILE:			MyAI.py
#
# AUTHOR: 		Justin Chung
#
# DESCRIPTION:	This file contains the MyAI class. You will implement your
#				agent in this file. You will write the 'getAction' function,
#				the constructor, and any additional helper functions.
#
# NOTES: 		- MyAI inherits from the abstract AI class in AI.py.
#
#				- DO NOT MAKE CHANGES TO THIS FILE.
# ==============================CS-199==================================

from AI import AI
from Action import Action
from collections import defaultdict


class MyAI(AI):

    def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
        ########################################################################
        #							YOUR CODE BEGINS						   #
        ########################################################################
        self.rows = colDimension
        self.cols = rowDimension
        self.mines = totalMines
        self.curX = startX
        self.curY = startY

        # U = uncovered + covered + safe
        self.uncovered = set()  # set of covered cells
        self.covered = set()    # set of covered cells
        self.safe = set()       # set of cells that are safe to uncover
        self.numbers = set()    # set of uncovered cells with numbers (subset of uncovered)
        self.frontier = set()   # set of cells that neighbors an uncovered cell (subset of covered, neighbors of numbers)

        # initialize the board
        self.board = []
        for i in range(self.rows):
            self.board.append([0] * self.cols)

        # add uncovered cell to set
        self.uncovered.add((self.curX, self.curY))

        # add covered cells to set
        for x in range(self.rows):
            for y in range(self.cols):
                self.covered.add((x, y))
        self.covered.remove((self.curX, self.curY))

        # add neighbors to frontier
        self.setNeighbors(self.curX, self.curY, self.toFrontier)

    ########################################################################
    #							YOUR CODE ENDS							   #
    ########################################################################

    def getAction(self, number: int) -> "Action Object":
        ########################################################################
        #							YOUR CODE BEGINS						   #
        ########################################################################
        # add bomb count to cell (default cell value is 0)
        self.board[self.curX][self.curY] += number
        # self.printBoard()

        # no bombs nearby, move neighbors to safe set
        if self.board[self.curX][self.curY] == 0:
            self.setNeighbors(self.curX, self.curY, self.setSafe)
        # otherwise, move cell to numbers set and neighbors to frontier
        else:
            self.numbers.add((self.curX, self.curY))
            self.setNeighbors(self.curX, self.curY, self.toFrontier)

        # No safe cells, find corners in numbers set
        if len(self.safe) == 0:
            # print("NO SAFE CELLS, CHECK CORNERS")
            self.checkCorners()

        if len(self.safe) == 0:
            # print("NO SAFE CELLS, CHECK FRONTIER")
            self.checkFrontier()

        if len(self.safe) == 0:
            # print("NO SAFE CELLS, USE INFERENCE")
            self.useInference()

        # All mines are founds, set all covered cells safe
        if self.mines == 0 and len(self.covered) > 0:
            self.safe.update(self.covered)
            self.covered = set()

        # If there are safe cells
        if len(self.safe) != 0:
            self.curX, self.curY = self.safe.pop()

            # remove from frontier
            self.frontier.discard((self.curX, self.curY))

            # uncover a cell
            self.uncovered.add((self.curX, self.curY))
            return Action(AI.Action.UNCOVER, self.curX, self.curY)

        # check for board completion
        if self.mines == 0:
            # no more mines
            return Action(AI.Action.LEAVE)
        else:
            notFrontier = self.covered.difference(self.frontier)

            # if mines left <= maximum possible mines in frontier
            if self.mines <= self.estimateMines() and len(notFrontier) > 0:
                # select from covered that's not in frontier
                self.curX, self.curY = notFrontier.pop()
                self.covered.discard((self.curX, self.curY))
                # print(f'Uncovered by inference {self.curX + 1, self.curY + 1}')
            else:
                # uncover a cell using probability
                bestCell = self.getBestCell()
                if bestCell is not None:
                    self.curX, self.curY = bestCell
                    # remove from covered and frontier
                    self.covered.discard((self.curX, self.curY))
                    # print(f'Uncovered by probability {self.curX + 1, self.curY + 1}')

                else:
                    # uncover random cell
                    self.curX, self.curY = self.covered.pop()
                    # print(f'Randomly uncovered {self.curX + 1, self.curY + 1}')

            # remove from frontier
            self.frontier.discard((self.curX, self.curY))

            # uncover a cell
            self.uncovered.add((self.curX, self.curY))

            return Action(AI.Action.UNCOVER, self.curX, self.curY)

    ########################################################################
    #							YOUR CODE ENDS							   #
    ########################################################################

    def getNum(self, x: int, y: int):
        """ get number of mines at (x,y), -1 if out of bounds """
        if 0 <= x < self.rows and 0 <= y < self.cols:
            return self.board[x][y]
        return -1

    def setNeighbors(self, x: int, y: int, func):
        """ use function on all neighbors of (x,y) """
        func(x - 1, y - 1)
        func(x - 1, y)
        func(x - 1, y + 1)
        func(x, y - 1)
        func(x, y + 1)
        func(x + 1, y - 1)
        func(x + 1, y)
        func(x + 1, y + 1)

    def toFrontier(self, x: int, y: int):
        """ Add a covered cell to frontier """
        if (x, y) in self.covered:
            self.frontier.add((x, y))

    def setSafe(self, x: int, y: int):
        """ move (x,y) from covered to the safe set """
        # move to safe if still covered
        if (x, y) in self.covered:
            # print(f'Setting ({x + 1}, {y + 1}) as safe')
            self.safe.add((x, y))

            # remove from covered set
            self.covered.remove((x, y))

    def setMine(self, x: int, y: int):
        """ move (x,y) to mines and reduce bomb count of neighbors by 1"""
        # invalid coordinates, (x,y) is not a covered cell
        if (x, y) not in self.covered:
            return

        # print(f'Setting ({x+1}, {y+1}) as bomb')

        # mark cell as uncovered ("bomb") and reduce bomb count of neighbors by 1
        self.covered.remove((x, y))
        self.uncovered.add((x, y))
        self.board[x][y] -= 1
        self.mines -= 1
        self.frontier.discard((x, y))

        # remove 1 from neighbor's bomb counts and update status
        self.setNeighbors(x, y, self.minusOne)
        self.setNeighbors(x, y, self.updateNumber)

    def minusOne(self, x: int, y: int):
        """ Remove 1 from (x,y)'s mines counts """
        if 0 <= x < self.rows and 0 <= y < self.cols:
            self.board[x][y] -= 1

    def updateNumber(self, x: int, y: int):
        """ check if cell is cleared (remove from numbers) and make neighbors safe if so """
        # numbered cell is now safe
        if (x, y) in self.numbers and self.board[x][y] == 0:
            # remove from numbers
            self.numbers.remove((x, y))

            self.setNeighbors(x, y, self.setSafe)

    def clearedAdjacent(self, x: int, y: int):
        """ find the number of cleared cells and mines directly next to (x,y) """
        num = 0
        if (x-1, y) in self.uncovered and self.board[x-1][y] <= 0:
            num += 1
        if (x+1, y) in self.uncovered and self.board[x+1][y] <= 0:
            num += 1
        if (x, y+1) in self.uncovered and self.board[x][y+1] <= 0:
            num += 1
        if (x, y-1) in self.uncovered and self.board[x][y-1] <= 0:
            num += 1

        return num

    def checkCorners(self):
        """ Find potential corner bombs and update safe set """
        mines = set()
        for x, y in self.numbers:
            if self.board[x][y] == 1 and self.clearedAdjacent(x, y) == 2 and len(self.frontierNeighbors(x, y)) == 1:
                # print(f'Potential corner found at {x+1} {y+1}')
                # print(self.getNum(x, y+1), self.getNum(x, y-1),self.getNum(x+1, y),self.getNum(x-1, y))

                # top cell is not 0
                if self.getNum(x, y+1) > 0:
                    # check left:
                    if self.getNum(x-1, y) > 0:
                        mines.add((x-1, y+1))
                    # check right
                    elif self.getNum(x+1, y) > 0:
                        mines.add((x+1, y+1))
                # bottom cell is not 0
                elif self.getNum(x, y-1) > 0:
                    # check left:
                    if self.getNum(x-1, y) > 0:
                        mines.add((x-1, y-1))
                    # check right:
                    elif self.getNum(x+1, y) > 0:
                        mines.add((x+1, y-1))

        # add mines
        if len(mines) != 0:
            # print(f'{len(mines)} mine(s) detected')

            for x, y in mines:
                self.setMine(x, y)

    def frontierNeighbors(self, x: int, y: int) -> set:
        """ find a set of neighbors in the frontier """
        neighbors = set()

        if (x, y+1) in self.frontier:
            neighbors.add((x, y+1))
        if (x, y-1) in self.frontier:
            neighbors.add((x, y-1))
        if (x+1, y+1) in self.frontier:
            neighbors.add((x+1, y+1))
        if (x+1, y) in self.frontier:
            neighbors.add((x+1, y))
        if (x+1, y-1) in self.frontier:
            neighbors.add((x+1, y-1))
        if (x-1, y+1) in self.frontier:
            neighbors.add((x-1, y+1))
        if (x-1, y) in self.frontier:
            neighbors.add((x-1, y))
        if (x-1, y-1) in self.frontier:
            neighbors.add((x-1, y-1))

        return neighbors

    def checkFrontier(self):
        """ Check if cell in numbers matches number of neighbors in frontier """
        mines = set()

        for (x, y) in self.numbers:
            frontierNeighbors = self.frontierNeighbors(x, y)
            if self.board[x][y] == len(frontierNeighbors):
                # set frontier neighbors to mines
                for (fx, fy) in frontierNeighbors:
                    mines.add((fx, fy))

        # add mines
        if len(mines) != 0:
            # print(f'{len(mines)} mine(s) detected')

            for x, y in mines:
                self.setMine(x, y)

    def numberNeighbors(self, x: int, y: int) -> set:
        """ find a set of neighbors in the numbers set """
        neighbors = set()

        if (x, y + 1) in self.numbers:
            neighbors.add((x, y + 1))
        if (x, y - 1) in self.numbers:
            neighbors.add((x, y - 1))
        if (x + 1, y + 1) in self.numbers:
            neighbors.add((x + 1, y + 1))
        if (x + 1, y) in self.numbers:
            neighbors.add((x + 1, y))
        if (x + 1, y - 1) in self.numbers:
            neighbors.add((x + 1, y - 1))
        if (x - 1, y + 1) in self.numbers:
            neighbors.add((x - 1, y + 1))
        if (x - 1, y) in self.numbers:
            neighbors.add((x - 1, y))
        if (x - 1, y - 1) in self.numbers:
            neighbors.add((x - 1, y - 1))

        return neighbors

    def useInference(self):
        """ Use inference to detected if adjacent numbers can have safe cells or mines in their uncovered neighbors """
        mines = set()
        safe = set()

        # Loop through numbers
        for (x, y) in self.numbers:
            # set of neighbors in the frontier
            fNeighbors = self.frontierNeighbors(x, y)

            # The number of mines is 1 less than num of neighbors
            if len(fNeighbors) == self.board[x][y] + 1:
                # all numbers that share a frontier cell with (x, y)
                nNeighbors = defaultdict(int)
                for x2, y2 in fNeighbors:
                    for neighbor in self.numberNeighbors(x2, y2):
                        if neighbor != (x, y):
                            nNeighbors[neighbor] += 1

                # Loop through each neighbor in numbers that neighbors at least 2 of the frontier cells
                for (x2, y2), count in nNeighbors.items():
                    if count != 2:
                        continue

                    # set of frontier neighbors for each neighbor in numbers
                    nNeighborsF = self.frontierNeighbors(x2, y2)

                    # neighbors that have 2 frontier neighbor overlaps must have a bomb there
                    diffNeighbors = nNeighborsF.difference(fNeighbors)

                    if self.board[x2][y2] == 1:
                        # frontier neighbors that are not overlaps are safe
                        safe.update(diffNeighbors)
                    elif self.board[x2][y2] - self.board[x][y] == len(diffNeighbors):
                        # all non overlap frontier neighbors are mines
                        mines.update(diffNeighbors)

        # add safe cells
        if len(safe) != 0:
            # print(f'{len(safe)} cell(s) set safe')

            for x, y in safe:
                self.setSafe(x, y)

        # add mines
        if len(mines) != 0:
            # print(f'{len(mines)} mine(s) detected')

            for x, y in mines:
                # print("SET MINE", x+1, y+1)
                self.setMine(x, y)

    def estimateMines(self) -> int:
        """ Returns the maximum number of mines the current frontier contains """
        total = 0
        checked = set()
        for x, y in self.numbers:
            if (x, y) in checked:
                continue

            # get neighbors
            fNeighbors = self.frontierNeighbors(x, y)
            nNeighbors = self.numberNeighbors(x, y)

            # for all numbers that have not been considered
            mines = 0
            for x2, y2 in nNeighbors.difference(checked):
                nNeighborsF = self.frontierNeighbors(x2, y2)

                # neighbor's frontier is not subset of this cell's frontier
                if not nNeighborsF.issubset(fNeighbors):
                    # add neighbor's mine count
                    mines += self.board[x2][y2]

            total += max(mines, self.board[x][y])

            # Mark cells as checked
            checked.add((x, y))
            checked.update(nNeighbors)

        return total

    # def printBoard(self):
    #     """ Displays the board """
    #     for y in reversed(range(self.cols)):
    #         for x in range(self.rows):
    #             print(f'{self.board[x][y]:>2}', end=" ")
    #         print()

    def getBestCell(self) -> ():
        """return a cell with the lowest possibility to be a mine"""
        # probability of mines in covered
        lowestProb = self.mines / len(self.covered)

        bestCell = None

        for (x, y) in self.numbers:
            neighbors = self.frontierNeighbors(x, y)
            if len(neighbors) != 0:
                # check mines probability
                prob = self.board[x][y] / len(neighbors)
                if prob < lowestProb:
                    lowestProb = prob

                    # get a random cell in neighbors
                    bestCell = neighbors.pop()

        # if all numbers have worse odds, pick from a cell not in frontier
        if bestCell is None:
            notFrontier = self.covered.difference(self.frontier)
            if len(notFrontier) > 0:
                bestCell = notFrontier.pop()

        return bestCell
