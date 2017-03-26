import threading
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from DataManager import DataManager
from math import sqrt


class App:
    # map
    loaded_map = []  # Loaded map. 2d array of numbers
    puzzle = []  # list containing unedited puzzle, StringVars
    # gui
    solution = []  # list containing solluton eg. puzzle to edit, StringVars
    solution_widgets = []  # Labels
    tries = None  # IntVar. number of /solve/ calls
    depth = None  # IntVar. depth
    # solving thread
    th = None  # solving thread
    restarting = False  # enabled shortcut for solving thread
    counter_lock = threading.Lock()  # lock to access steps_to_do
    no_more_steps = threading.Event()  # flag for locking solving thread
    steps_to_do = 0  # steps to do

    size = 0  # number of columns
    block = 0  # size block = sqrt(size) for faster checking. If map is 9x9 block is 3x3

    def __init__(self, root):
        # if you want to have clear view, change Frame to LabelFrame
        # and optional add text kparam
        mainframe = Frame(root)
        mainframe.pack(padx=10, pady=10)

        left_panel = Frame(mainframe)
        left_panel.grid(row=0, column=0, sticky=N+W)

        info_panel = Frame(left_panel)
        info_panel.grid(column=0, row=1, sticky=N+W)

        depth_panel = LabelFrame(info_panel, text='Depth')
        depth_panel.grid(row=0, column=1, padx=5)
        self.depth = IntVar(value=0)                        # inits depth
        Label(depth_panel, textvariable=self.depth).pack()

        iter_panel = LabelFrame(info_panel, text='Calls')
        iter_panel.grid(row=0, column=0)
        self.tries = IntVar(value=-1)                       # inits tries
        Label(iter_panel, textvariable=self.tries).pack()

        puzzle_panel = LabelFrame(left_panel, text='Puzzle')
        puzzle_panel.grid(row=0, column=0)

        self.s_frame = Frame(puzzle_panel)
        self.s_frame.grid(sticky=NSEW, padx=5, pady=5)

        # ttk.Separator(mainframe, orient=VERTICAL).grid(row=0, column=1, sticky=N + S, padx=5)
        right_panel = Frame(mainframe)
        right_panel.grid(row=0, column=2, sticky=NS, padx=5)

        self.b_frame = LabelFrame(right_panel, text='Steps')  # buttons frame
        self.b_frame.grid(row=0, column=2, sticky=N)

        self.m_frame = LabelFrame(right_panel, text='Menu')  # Menu frame
        self.m_frame.grid(row=1, column=2, sticky=N)

        def step(x):
            # Helper function to add steps
            return lambda: self.change_steps(add=x)

        # buttons for adding steps
        for y, num in enumerate([[1, 1], [10, 10], [100, 100], ['All', 9999999]]):
            Button(self.b_frame, text=num[0], width=5, padx=5, command=step(num[1])).grid(column=0, row=y, padx=5, pady=5)

        # menu buttons
        Button(self.m_frame, text='Restart', width=5, padx=5, command=self.restart).grid(row=0,  padx=5, pady=5)
        Button(self.m_frame, text='Load', width=5, padx=5, command=self.load).grid(row=1, padx=5, pady=5)


        # default sudoku
        self.loaded_map =  [[0, 0, 0, 0],
                            [0, 3, 2, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 0]]
        #restarts
        self.restart()

    def start(self):
        """Starts serching"""
        print('Starting start')
        if self.solve():
            print('Solution found')
        else:
            print('This sudoku is invalid!')
        self.restarting = False
        self.th = None

    def load(self):
        """Loads json array from file"""
        # loading maps bigger than 9x9 may give weird
        # effect because of widgets resizing
        path = askopenfilename(filetypes=(
                            ('Sudoku map', '*.sudoku'),
                            ('All files', '*.*')))
        try:
            new_map = DataManager.get(path)
            self.loaded_map = new_map
        except DataManager.InvalidMap and UnicodeDecodeError as ee:
            print('Wrong formatting or file not found.', file=sys.stderr)
            print('Searched {}'.format(path))
        finally:
            print('Restarting', file=sys.stderr)
            self.restart()

    def restart(self):
        """Restarts and inits sudoku solver"""
        if not self.th:
            # solving thread exited
            print('Restarting...')
            puzzle = self.loaded_map

            # inits new matrix to work with
            self.puzzle = self.to_trinket_var(puzzle)
            self.solution = self.to_trinket_var(puzzle)

            # destroy display widgets
            [label.destroy() for label in self.solution_widgets]
            self.solution_widgets = []

            # makes new display widgets
            self.display_nums()

            # inits variables
            self.restarting = False
            self.size = len(self.solution)
            self.block = int(sqrt(self.size))
            self.tries.set(0)  # created in __init__
            self.steps_to_do = IntVar(value=0)
            self.no_more_steps.clear()
            # self.depth is in __init__ because it
            # need access to root before everything

            # makes solving thread
            th = threading.Thread(target=self.start)
            self.th = th
            th.start()
        else:
            # Joining thread block everything forever.
            # Maybe main thread needs to be active?
            if not self.restarting: self.change_steps(set_to=99999)  # adds infinite steps
            self.restarting = True  # enable shortcut

            root.after(10, self.restart)  # callback itself to check if thread exited


    def display_nums(self):
        """Makes Label widgets for displaying sudoku as a table"""
        # Putting blank image in label give access
        # to make height and width in pixels
        i = PhotoImage()
        for row, aa in enumerate(self.solution):
            for col, num in enumerate(aa):
                if self.puzzle[row][col].get() != ' ':
                    color = 'lightgreen'
                else:
                    color = root.cget("background")

                # textvariable is what updates the text in label
                lb = Label(self.s_frame, text=num.get(), textvariable=num, width=25, height=25, image=i, borderwidth=2, compound='center', relief=SUNKEN, bg=color)
                lb.grid(row=row, column=col)
                self.solution_widgets.append(lb)

    @staticmethod
    def to_trinket_var(seq):
        """changes 2d list of numbers to list of StringVar
        0 is replaced to ' ' """
        def make_var(num):
            # helper functions for making StringVars
            num = ' ' if num == 0 else num
            new_num = StringVar()
            new_num.set(num)
            return new_num

        # change a list of numbers to list of IntVar
        # with that the sudoku display can by dynamically updated
        return [[make_var(num) for num in row] for row in seq]

    def change_steps(self, add=None, set_to=None):
        """Changes number of steps"""
        self.counter_lock.acquire()
        if add is not None and set_to is None:
            # n = self.steps_to_do.get()
            # n = 1 if self.steps_to_do.get() > 0 else 0  # just to don't do -1
            self.steps_to_do.set(self.steps_to_do.get() + add)  # changes number of steps
        else:
            print(self.steps_to_do.get(), set_to)
            self.steps_to_do.set(set_to)
            print(self.steps_to_do.get())
        if self.steps_to_do.get() > 0:
            self.no_more_steps.set()
        self.counter_lock.release()

    def locker(self):
        """Lock solving thread in place"""
        if self.steps_to_do.get() <= 0:
            # no more steps for you to do
            print('Thread: No more steps')
            self.no_more_steps.clear()
            self.no_more_steps.wait()  # waits for more steps
            print('Thread: Resuming serching')
        self.change_steps(-1)

    def call_counter(ff):
        """Count depth, tries and calls solve()"""
        def helper(self, *args, **kwargs):
            self.locker()  # locks thread and counts number of iterations]
            self.depth.set(self.depth.get() + 1)  # depth + 1
            self.tries.set(self.tries.get() + 1)  # add to counter
            res = ff(self, *args, **kwargs)  # calls call_counter
            self.depth.set(self.depth.get() - 1)  # depth + 1
            return res
        return helper

    @call_counter
    def solve(self, num_row=None, num_col=None):
        """recursive solves the sudoku"""
        if self.restarting:
            # shortcut for restarting
            print('Shortcut!!')
            return True

        if num_row is None and num_col is None:
            # finds starting point
            num_row, num_col = self.next_free()

        if num_row is False:
            # solution found!
            return True

        for new_num in range(1, self.size + 1):
            # iterrates over every possible number
            if self.fits(new_num, num_row, num_col):
                # number fits in sudoku
                self.solution[num_row][num_col].set(str(new_num))  # sets /new number/
                if self.solve(*self.next_free()):  # goes deeper
                    return True  # solution found!
                self.solution[num_row][num_col].set(' ')  # unsets /new number/

        return False  # triggers backtracking

    def fits(self, number, num_row, num_col):
        """Check if number fits in row and col"""
        number = str(number)
        nums = set()
        for i in range(self.size):
            # i really wanted to to this with sets
            nums.add(self.solution[num_row][i].get())
            nums.add(self.solution[i][num_col].get())
        if number in nums:
            return False

        # check if /number/ exists in block
        block = self.block
        row_shift = (num_row // block) * block
        col_shift = (num_col // block) * block
        for row in range(block):
            for col in range(block):
                if self.solution[row + row_shift][col + col_shift].get() == number:
                    # it is
                    return False
        # everything passed
        return True

    def next_free(self):
        """finds first free spot for a number"""
        for x, row in enumerate(self.solution):
            for y, col in enumerate(row):
                if col.get() == ' ':
                    return x, y
        return False, False

if __name__ == '__main__':
    root = Tk()
    root.wm_title("Solver")
    app = App(root)
    mainloop()


