import sys

from crossword import Variable
from crossword import Crossword
from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for variable in self.domains.keys():
            for word in self.domains[variable].copy() or set():
                if variable.length != len(word):
                    self.domains[variable].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revisions = False
        
        if self.crossword.overlaps[x, y] == None: 
            return False
        else: 
            posX, posY = self.crossword.overlaps[x, y]
        
        possibleLetters = set()
        for word in self.domains[y]:
            if word[posY] not in possibleLetters:
                possibleLetters.add(word[posY])
        for word in self.domains[x].copy():
            if word[posX] not in possibleLetters:
                self.domains[x].remove(word)
                revisions = True
                
        return revisions
        raise NotImplementedError

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs == None: #initiate arcs to be a list of all edges
            arcs = list()
            for x in self.domains:
                for y in self.domains: 
                    if x == y or self.crossword.overlaps[x, y] == None: continue #if x and y don't overlap or are referencing the same variable, skip
                    arcs.append((x, y)) #add both ways to remove from both sides
                    arcs.append((y, x))
            return self.ac3(arcs)
        
        while (arcs):
            currentArc = arcs.pop()
            x = currentArc[0]
            y = currentArc[1]
            
            if(self.revise(x, y)):
                if not self.domains[x]: return False
                for y in self.domains:
                    if x == y or self.crossword.overlaps[x, y] == None: continue
                    arcs.append((y, x)) #if y neighbors x, y may change because of a change in x (may be less words to choose from)
        
        return True
        raise NotImplementedError

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for variable in self.domains:
            if variable not in assignment.keys(): #if there exists a value that is not assigned, it is not complete (so it returns false)
                return False
        
        return True #every variable has exactly 1 word corresponding to it
        raise NotImplementedError

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        chosenWords = set()
        for variable in assignment.keys():
            word = assignment[variable]
            
            #fail condition: length of word is different from length of slot
            if variable.length != len(word):
                return False
            
            #fail condition: word is not unique
            if word in chosenWords:
                return False
            chosenWords.add(word)
            
            #fail condition: there exists a neighbor with a different letter in same position
            for neighbor in self.crossword.neighbors(variable): #for every neighbor (has overlap)
                if(neighbor in assignment.keys()): #skip if neighbor doesn't already have a word chosen
                    pos = self.crossword.overlaps[variable, neighbor] 
                    neighborWord = assignment[neighbor] 
                    if word[pos[0]] != neighborWord[pos[1]]: #check for conflicts
                        return False
                
        return True
        raise NotImplementedError

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        eliminations = dict()
        
        for word in self.domains[var]: 
            eliminations[word] = 0 #every word initially has 0 changes
            for neighbor in self.crossword.neighbors(var):
                if neighbor in assignment.keys(): 
                    continue
                posX = self.crossword.overlaps[var, neighbor][0]
                posY = self.crossword.overlaps[var, neighbor][1]
                for neighborWord in self.domains[neighbor]:
                    if word[posX] == neighborWord[posY]:
                        eliminations[word] += 1
        
        return sorted(eliminations, reverse=True)
        raise NotImplementedError

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        chosen_variable = next(var for var in self.domains if var not in assignment) #chooses any unassigned variable to start
        remaining_values = len(self.domains[chosen_variable]) #amount of words that can be chosen (starts as the value from the random variable)
        degree = len(self.crossword.neighbors(chosen_variable)) #amount of neighbors (to be used in event of tie) (starts with value from random variable)
        
        
        for variable in self.domains:
            if variable not in assignment.keys():
                if len(self.domains[variable]) < remaining_values: #finding the least amount of options available
                    chosen_variable = variable 
                    remaining_values = len(self.domains[variable])
                    degree = len(self.crossword.neighbors(variable))
                elif len(self.domains[variable]) == remaining_values: #in event of tie, highest degree (num of neighbors)
                    if len(self.crossword.neighbors(variable)) > degree: #in the event of another tie, it will ignore this to save time (since it can be any)
                        chosen_variable = variable 
                        degree = len(self.crossword.neighbors(variable))

        return chosen_variable #returns the most optimal variable to crawl to next
        raise NotImplementedError

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment        
        var = self.select_unassigned_variable(assignment)
        
        for word in self.order_domain_values(var, assignment): #loop through all possible words
            assignment[var] = word
            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result == assignment: return result
            assignment[var] = None 
        return None
        raise NotImplementedError


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
