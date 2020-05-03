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

pd.set_option("display.width", 150)
pd.set_option("display.max_columns", 30)


# Simple formulation as normal LP. It's not yet entirely clear if this
# is actually working. The practice density stuff above is especially problematic.
class SimplePracticeScheduleSolver(LpProblem):
    # Note: time available per slot
    def __init__(self, name, n_items, n_slots, time_avail, erg_avail,
                 time_per, erg_used,
                 win_sz=10, min_per_win=1, max_per_win=4,
                 item_names=None):
        LpProblem.__init__(self, name, LpMinimize)
        self.n_items = n_items    # study items
        self.n_slots = n_slots    # time slots
        self.time_avail = time_avail
        self.time_per = time_per
        self.erg_used = erg_used
        self.win_sz = win_sz
        self.min_per_win = min_per_win
        self.max_per_win = max_per_win
        self.practice = {}        # (s, t) => Variable (amount of practice)
        self.erg = [None]*self.n_slots
        self.erg_inc = {}         # (s, t) => Energy increase
        self.erg_dec = {}         # (s, t) => Energy decrease
        self.time_so_far = {}     # (s, t) => Variable (amount of practice up to that point)
        if item_names is None:
            item_names = ["item" + "_" + str(i) for i in range(0, n_items)]
        self.item_names = item_names
        self.total_practice_time = None
        self.item_timeliness_metric = None
        self.erg_deltas = None
        self.erg_deltas = 0

    def build(self):
        # Variables - two-dimensional array tasks x time slot
        for i in range(0, self.n_items):
            for t in range(0, self.n_slots):
                self.practice[(i, t)] = LpVariable("P_{}_{}".format(i, t), cat='Integer', lowBound=0)
                self.time_so_far[(i, t)] = LpVariable("T_{}_{}".format(i, t), lowBound=0)
        # Energy usage variables
        for t in range(0, self.n_slots):
            self.erg_inc[t] = LpVariable("ERGINC_{}".format(t), lowBound=0)
            self.erg_dec[t] = LpVariable("ERGDEC_{}".format(t), lowBound=0)
        # Objective function - minimize overall practice time for now
        self.total_practice_time = total_practice_time = sum(self.practice[(i, t)] for i in range(0, self.n_items) for t in range(0, self.n_slots))
        # and push things as far left as possible (does this work?)
        self.item_timeliness_metric = item_timeliness_metric = sum(self.time_so_far[(i, t)] for i in range(0, self.n_items) for t in range(0, self.n_slots))
        # Energy used each day
        for t in range(0, self.n_slots):
            self.erg[t] = sum(self.erg_used[i]*self.practice[i, t] for i in range(0, self.n_items))


        self.erg_deltas = sum((self.erg_inc[t] + self.erg_dec[t]) for t in range(0, self.n_slots))

        # Objective is to use the least amount of resource to complete tasks in
        # as timely a manner as possible while maximizing fun on a given day (i.e., ensuring a mix of boring
        # and non-boring tasks.
        self.objective = total_practice_time + self.erg_deltas - self.item_timeliness_metric
        # Constraints
        # Total time across tasks less than that available within a time slot (e.g., might be hours/day)
        for t in range(0, self.n_slots):
            self += sum(self.practice[(i, t)] for i in range(0, self.n_items)) <= self.time_avail[t]
        # Like above except for energy
        for t in range(0, self.n_slots):
            self += sum(self.practice[(i, t)] for i in range(0, self.n_items)) <= self.time_avail[t]
        # Required time for each task.
        for i in range(0, self.n_items):
            self += sum(self.practice[(i, t)] for t in range(0, self.n_slots)) >= self.time_per[i]
        # Definition of time so (we maximize sum of totals so far which tends to push to left.
        # Need to study this behavior more closely.
        for i in range(0, self.n_items):
            for t in range(0, self.n_slots):
                self += (self.time_so_far[(i, t)] == sum(self.practice[(i, t0)] for t0 in range(0, t-1)))

        # Energy delta definition
        for i in range(0, self.n_items-1):
            for t in range(0, self.n_slots-1):
                self += (self.erg_inc[t+1] - self.erg_dec[t+1]) == (self.erg[t+1] - self.erg[t])


        # Required rest periods per study item (independent of time studied at the moment)
        # Use a sliding window approximation. At least one practice session in every
        # window, and at least one rest. Sort of local density.
        for i in range(0, self.n_items):
            for t in range(0, self.n_slots - self.win_sz):
                self += sum(self.practice[(i, t+t_delta)] for t_delta in range(0, self.win_sz)) >= self.min_per_win
                self += sum(self.practice[(i, t+t_delta)] for t_delta in range(0, self.win_sz)) <= self.max_per_win




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


    def get_solution_timeliness_values(self):
        return [sum(value(self.time_so_far[(i, t)])
                    for t in range(0, self.n_slots)) for i in range(0, self.n_items)]

    def get_total_time_per_values(self):
        return [sum(value(self.practice[(i, t)])
                    for t in range(0, self.n_slots)) for i in range(0, self.n_items)]

    def get_solution_as_df(self, start_time=None):
        day_of_week = ["Su", "M", "T", "W", "Th",
                       "Fr", "Sa"]
        if start_time is None:
            start_time = datetime.datetime.now() + datetime.timedelta(days=1)
        m = self.get_solution()
        data = dict({})
        data["name"] = self.item_names
        for t in range(0, self.n_slots):
            date_string = (start_time + t * datetime.timedelta(days=1)).strftime("%m/%d")
            date_string = day_of_week[(start_time + t * datetime.timedelta(days=1)).isoweekday()-1] + ", " + date_string
            data[date_string] = m[:, t]
        df = pd.DataFrame(data)

        return df


def solve(n_items, time_avail, erg_avail, time_per, erg_used, win_sz=10, min_per_win=1,
          max_per_win=4, item_names=None, min_slots=1, max_slots=40, show_solutions=False):
    n_slots = min_slots
    if VERBOSE:
        logging.info("Solving problem with the parameters:")
        logging.info("  n_items = {}".format(n_items))
        logging.info("  time_avail = {}".format(time_avail))
        logging.info("  time_avail = {}".format(erg_avail))
        logging.info("  time_per  = {}".format(time_per))
        logging.info("  erg_used   = {}".format(erg_used))

    while n_slots <= max_slots:
        if VERBOSE:
            logging.info("Attempting to solve problem with {} time slots available. ".format(n_slots))
        solver = SimplePracticeScheduleSolver("test",
                                              n_items=n_items,
                                              n_slots=n_slots,
                                              time_avail=time_avail,
                                              erg_avail=erg_avail,
                                              time_per=time_per,
                                              erg_used=erg_used,
                                              win_sz=win_sz,
                                              min_per_win=min_per_win,
                                              max_per_win=max_per_win,
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
                         time_avail=[5]*50,
                         erg_avail=[5]*50,
                         time_per=[5]*25,
                         erg_used=[1] * 25,
                         win_sz=7,
                         min_per_win=1,
                         max_per_win=3)


config_problem1 = _config(n_items=10,
                          time_avail=[5]*50, # FIXME: Better way to handlle this?
                          erg_avail=[5]*50,
                          time_per=[5, 3, 2, 3, 2, 3, 2, 2, 2, 4],
                          erg_used=[0, 10, 2, 10, 2, 19, 2, 10, 2, 10],
                          win_sz=5,
                          min_per_win=1,
                          max_per_win=3,
                          item_names=["Hard", "Easy"]*5)


config_small = _config(n_items=4,
                       time_avail=[2]*50,
                       erg_avail=[5]*50,
                       time_per=[2]*25,
                       erg_used=[1, 2, 1, 2]*25,
                       item_names=["Easy", "Hard", "Easy", "Hard"],
                       win_sz=3,
                       min_per_win=1,
                       max_per_win=2)


config_test = {'n_items': 10,
               'time_avail': [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
               'erg_avail': [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
               'time_per': [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
               'erg_used': [1, 2, 2, 1, 2, 1, 2, 1, 2, 1],
               'item_names': ['Phrase-1', 'Phrase-2', 'Phrase-3', 'Phrase-4', 'Phrase-5', 'Phrase-6', 'Phrase-7', 'Phrase-8', 'Phrase-9', 'Phrase-10'],
               'win_sz': 3, 'min_per_win': 1, 'max_per_win': 2}


def show_solution(solver):
    pd.set_option("display.max_columns", 50)
    pd.set_option("display.width", 120)
    print("Schedule starting tomorrow:")
    print(solver.get_solution_as_df())
    repractice_tot_min = 0
    repractice_tot_actual = 0
    for i in range(0, solver.n_items):
        num = value(sum(solver.practice[i, t] for t in range(0, solver.n_slots)))
        ratio = solver.time_per[i]/num
        repractice_tot_actual += value(sum(solver.practice[i, t] for t in range(0, solver.n_slots)))
        repractice_tot_min += solver.time_per[i]
        print("item {} time efficiency = {}".format(i, ratio))
    print("Overall re-practice ratio is {}\n".format((repractice_tot_actual - repractice_tot_min)/repractice_tot_min))

if __name__ == "__main__":

    print("Minimum possible total time for config_small", sum(config_problem1["time_per"]))

    solver = solve(**config_test)
    show_solution(solver)

    solver2 = solve(**config_test, min_slots=15, max_slots=15)
    show_solution(solver2)

    #for slot_count in [4, 7, 12]:
    #    solver = solve(**config_small, min_slots=slot_count, max_slots=slot_count)
    #    if solver.status == LpStatusOptimal:
    #        show_solution(solver)

    if False:
        solver = solve(**config_sonata3)
        show_solution(solver)

    if False:
        print("Minimum possible total time", sum(config_problem1["time_per"]))
        solvers = []
        solver = solve(**config_problem1)
        solvers.append(solver)
        show_solution(solver)

        solver = solve(**config_problem1)
        solvers.append(solver)
        show_solution(solver)

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

