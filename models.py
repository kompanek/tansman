# Highly experimental. Trying to see what I can do within the constraints of an LP.
#
# - No notion of current learning state
# - Model based on time slots being filled
# - Moving window to ensure enough rest in given period
#
# Lots of opportunities for variation:
#   - Mental energy as a resource
#   - Better way of considering local utility (sum of "fun" currently maximized, alternatives?)
#
# Observations & Limitations
#
#  * I thought I'd see cases where tasks are repeated to meet density
#    requirements but this doesn't seem to happen in practice.
#
#  * Not sure how to tune density.
#
# * This is pretty slow once you have more than say 75 time slots.
#
# * Counter-intuitive feature of the model is that you have too many time slots
#   and you don't hit the minimum density of practice. Any way to make
#   slight improvement using just LP?
#
# *  There's no way to really model memory decay. I require a certain amount of
#    rest between study sessions involving a particular item, and put a cap
#    on that. My thought is that solve this as a 2-level problem.
#    Work in batches. Each batch is meant to get a set of items to
#    the next learning level. Then you get new parameters for that level.
#    Haven't implemented that yet.
#
# * No way to capture preferences on the diversity, no. of different things
#   studied. I may want to say penalize having too many *different* activities.
#   I think this is intrinsically non linear.
#   Not sure if it's possible to count non-zero values. Intuitively this doesn't
#   seem possible in an LP since it would involve a multiplicative term (binary variable
#   whether present and a value variable for "how much", and then a statement over the
#   sum of the binary variables, and a constraint relating them present=0 <=> "how much"==0).

import datetime
from pulp import *
import numpy as np
import pandas as pd
import logging
from colorama import Fore, Back, Style

# FIXME: Just turn off the logging altogether in R Studio. Real solution is to write
#   a logger that does something reasonable in R Studio.
VERBOSE = True

# Interesting. Not much sensitivity to these relative values
# Also interesting is that sometimes I see patterns but not always
# I think there's a random element in the solver
COEFF_TOTAL_PRACTICE_TIME = 1
COEFF_FUN_TOTAL = 1
COEFF_TIMELINESS = 1

pd.set_option("display.width", 150)
pd.set_option("display.max_columns", 30)


# Simple formulation as normal LP. It's not yet entirely clear if this
# is actually working. The practice density stuff above is especially problematic.
class SimplePracticeScheduleSolver(LpProblem):
    # Note: time available per slot
    def __init__(self, name, n_items, n_slots,  time_available, time_per_item, fun_per_item,
                 window_size=10, min_practice_per_window=1, max_practice_per_window=4,
                 item_names=None):
        LpProblem.__init__(self, name, LpMaximize)
        self.n_items = n_items    # study items
        self.n_slots = n_slots    # time slots
        self.time_available = time_available
        self.time_per_item = time_per_item
        self.fun_per_item = fun_per_item
        self.window_size = window_size
        self.min_practice_per_window = min_practice_per_window
        self.max_practice_per_window = max_practice_per_window
        self.practice = {}        # (s, t) => Variable (amount of practice)
        self.time_so_far = {}     # (s, t) => Variable (amount of practice up to that point)
        self.fun_level = {}       # (s, t) => Variable (metric corresponding to fun during that day/task)
        if item_names is None:
            item_names = ["item" + "_" + str(i) for i in range(0, n_items)]
        self.item_names = item_names
        self.total_practice_time = None
        self.item_timeliness_metric = None
        self.fun_total = None

    def build(self):
        # Variables - two-dimensional array tasks x time slot
        for i in range(0, self.n_items):
            for t in range(0, self.n_slots):
                self.practice[(i, t)] = LpVariable("P_{}_{}".format(i, t), lowBound=0)
                self.time_so_far[(i, t)] = LpVariable("T_{}_{}".format(i, t), lowBound=0)
                self.fun_level[(i, t)] = LpVariable("T_{}_{}".format(i, t), lowBound=0)
        # Objective function - minimize overall practice time for now
        self.total_practice_time = total_practice_time = sum(self.practice[(i, t)] for i in range(0, self.n_items) for t in range(0, self.n_slots))
        # and push things as far left as possible (does this work?)
        self.item_timeliness_metric = item_timeliness_metric = sum(self.time_so_far[(i, t)] for i in range(0, self.n_items) for t in range(0, self.n_slots))


        self.fun_total = fun_total = sum(self.fun_per_item[i]*self.practice[(i, t)] for i in range(0, self.n_items) for t in range(0, self.n_slots))




        # Objective is to use the least amount of resource to complete tasks in
        # as timely a manner as possible while maximizing fun on a given day (i.e., ensuring a mix of boring
        # and non-boring tasks.
        self.objective = COEFF_TIMELINESS*item_timeliness_metric + COEFF_FUN_TOTAL*fun_total - COEFF_TOTAL_PRACTICE_TIME*total_practice_time
        # Constraints
        # Total time across tasks less than that available within a time slot (e.g., might be hours/day)
        for t in range(0, self.n_slots):
            self += sum(self.practice[(i, t)] for i in range(0, self.n_items)) <= self.time_available[t]
        # Required time for each task.
        for i in range(0, self.n_items):
            self += sum(self.practice[(i, t)] for t in range(0, self.n_slots)) >= self.time_per_item[i]
        # Definition of time so (we maximize sum of totals so far which tends to push to left.
        # Need to study this behavior more closely.
        for i in range(0, self.n_items):
            for t in range(0, self.n_slots):
                self += (self.time_so_far[(i, t)] == sum(self.practice[(i, t0)] for t0 in range(0, t-1)))
        # Experimental - no more than 2 time units of study per slot per item
        # Primitive way to add "diversity"
        for i in range(0, self.n_items):
            for t in range(0, self.n_slots):
                self += self.practice[(i, t)] <= 2

        # Required rest periods per study item (independent of time studied at the moment)
        # Use a sliding window approximation. At least one practice session in every
        # window, and at least one rest. Sort of local density.
        for i in range(0, self.n_items):
            for t in range(0, self.n_slots - self.window_size - 1):
                self += sum(self.practice[(i, t+t_delta)] for t_delta in range(0, self.window_size)) >= self.min_practice_per_window
                self += sum(self.practice[(i, t+t_delta)] for t_delta in range(0, self.window_size)) <= self.max_practice_per_window

    def get_solution(self):
        status = self.solve()
        if status == LpStatusInfeasible:
            if VERBOSE:
                msg = "Infeasible. No solution for n_items={} and n_slots={}."
                logging.warning(msg.format(self.n_items, self.n_slots))
            return None
        schedule_matrix = np.zeros(shape=(self.n_items, self.n_slots))
        for i in range(0, self.n_items):
            for t in range(0, self.n_slots):
                schedule_matrix[i, t] = value(self.practice[(i, t)])
        return schedule_matrix

    def get_solution_fun_values(self):
        return [sum(self.fun_per_item[i] * value(self.practice[(i, t)])
                    for i in range(0, self.n_items)) for t in range(0, self.n_slots)]

    def get_solution_timeliness_values(self):
        return [sum(value(self.time_so_far[(i, t)])
                    for t in range(0, self.n_slots)) for i in range(0, self.n_items)]

    def get_total_time_per_item_values(self):
        return [sum(value(self.practice[(i, t)])
                    for t in range(0, self.n_slots)) for i in range(0, self.n_items)]

    def get_solution_as_df(self, start_time=None):
        if start_time is None:
            start_time = datetime.datetime.now() + datetime.timedelta(days=1)
        m = self.get_solution()
        data = dict({})
        data["name"] = self.item_names
        for t in range(0, self.n_slots):
            #data[str(t)] = m[:, t]
            date_string = (start_time + t * datetime.timedelta(days=1)).strftime("%m/%d")
            data[date_string] = m[:, t]
        df = pd.DataFrame(data)

        return df


def solve(n_items, time_available, time_per_item, fun_per_item, window_size=10, min_practice_per_window=1,
          max_practice_per_window=4, item_names=None, min_slots=1, max_slots=40):
    n_slots = min_slots
    if VERBOSE:
        logging.info("Solving problem with the parameters:")
        logging.info("  n_items = {}".format(n_items))
        logging.info("  time_available = {}".format(time_available))
        logging.info("  time_per_item  = {}".format(time_per_item))
        logging.info("  fun_per_item   = {}".format(fun_per_item))

    while n_slots <= max_slots:
        if VERBOSE:
            logging.info("Attempting to solve problem with {} time slots available. ".format(n_slots))
        solver = SimplePracticeScheduleSolver("test",
                                              n_items=n_items,
                                              n_slots=n_slots,
                                              time_available=time_available,
                                              time_per_item=time_per_item,
                                              fun_per_item=fun_per_item,
                                              window_size=window_size,
                                              min_practice_per_window=min_practice_per_window,
                                              max_practice_per_window=max_practice_per_window,
                                              item_names=item_names)
        solver.build()
        solution = solver.get_solution()
        if solution is not None:
            break
        n_slots = n_slots + 1
    return solver


def model_parameters(**kwargs):
    return _config(**kwargs)

def _config(**kwargs):
    return locals()['kwargs']


config_sonata3 = _config(n_items=25,
                         time_available=[5]*50,
                         time_per_item=[5]*25,
                         fun_per_item=[1]*25,
                         window_size=7,
                         min_practice_per_window=1,
                         max_practice_per_window=3)


config_problem1 = _config(n_items=10,
                          time_available=[5]*50, # FIXME: Better way to handlle this?
                          time_per_item=[5, 3, 2, 3, 2, 3, 2, 2, 2, 4],
                          fun_per_item=[0, 10, 2, 10, 2, 19, 2, 10, 2, 10],
                          window_size=5,
                          min_practice_per_window=1,
                          max_practice_per_window=3,
                          item_names=["Hard", "Easy"]*5)


config_small = _config(n_items=4,
                       time_available=[2]*50,
                       time_per_item=[2]*25,
                       fun_per_item=[1, 1, 2, 2]*25,
                       window_size=2,
                       min_practice_per_window=0,
                       max_practice_per_window=1)


def show_solution(solver):
    pd.set_option("display.max_columns", 50)
    pd.set_option("display.width", 120)
    print("Schedule starting tomorrow:")
    print(solver.get_solution_as_df())
    print("Fun by item")
    print(solver.get_solution_fun_values(), "Total of", sum(solver.get_solution_fun_values()))
    print("Timeliness by item")
    print(solver.get_solution_timeliness_values(), "Total of", sum(solver.get_solution_timeliness_values()))
    print("Total time by item")
    print(solver.get_total_time_per_item_values(), "Total of", sum(solver.get_total_time_per_item_values()))
    print("Objective function z = {}".format(value(solver.objective)))

    total_time = sum([value(solver.practice[(i, t)])
                      for i in range(0, solver.n_items) for t in range(0, solver.n_slots)])
    best_possible_time = sum(solver.time_per_item)
    print("Efficiency is {}/{} = {}".format(total_time, best_possible_time, total_time/best_possible_time))

    #print("Efficiency: minimum possible time over solution practice time: {}/{} = {}",
    #      sum(solver.time_per_item), sum([for v in value(solver.get_total_time_per_item_values()])
    #      sum(solver.time_per_item) / sum(value(solver.get_total_time_per_item_values()


if __name__ == "__main__":

    print("Minimum possible total time for config_small", sum(config_problem1["time_per_item"]))
    solver = solve(**config_small)
    show_solution(solver)

    if False:
        solver = solve(**config_sonata3)
        show_solution(solver)

    if False:
        print("Minimum possible total time", sum(config_problem1["time_per_item"]))
        solvers = []
        solver = solve(**config_problem1)
        solvers.append(solver)
        show_solution(solver)
    
        COEFF_FUN_TOTAL = 0
        solvers = []
        solver = solve(**config_problem1)
        solvers.append(solver)
        show_solution(solver)
    
        COEFF_FUN_TOTAL = 5
        solvers = []
        solver = solve(**config_problem1)
        solvers.append(solver)
        show_solution(solver)

    if False:

        # Experimenting
        config_problem2 = config_problem1.copy()
        config_problem2["min_slots"] = 12
        config_problem2["max_slots"] = 12
        solver = solve(**config_problem2)
        solvers.append(solver)
        show_solution(solver)

    if False:
        # Experimenting
        config_problem3 = config_problem1.copy()
        config_problem3["min_slots"] = 6
        config_problem3["max_slots"] = 6
        solver = solve(**config_problem3)
        solvers.append(solver)
        if solver.get_solution() is not None:
            show_solution(solver)

