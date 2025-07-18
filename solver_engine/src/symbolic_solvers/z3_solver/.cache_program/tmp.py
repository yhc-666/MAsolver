from z3 import *

fruits_sort, (Mangoes, Kiwis, Plums, Pears, Watermelons) = EnumSort('fruits', ['Mangoes', 'Kiwis', 'Plums', 'Pears', 'Watermelons'])
ranks_sort = IntSort()
ranks = [1, 2, 3, 4, 5]
fruits = [Mangoes, Kiwis, Plums, Pears, Watermelons]
rank = Function('rank', fruits_sort, ranks_sort)

pre_conditions = []
pre_conditions.append(Distinct([rank(f) for f in fruits]))
pre_conditions.append(rank(Kiwis) < rank(Plums))
pre_conditions.append(rank(Pears) == 3)
pre_conditions.append(rank(Kiwis) == 4)
pre_conditions.append(rank(Watermelons) == 1)
f0 = Const('f0', fruits_sort)
pre_conditions.append(ForAll([f0], And(1 <= rank(f0), rank(f0) <= 5)))

def is_valid(option_constraints):
    solver = Solver()
    solver.add(pre_conditions)
    solver.add(Not(option_constraints))
    return solver.check() == unsat

def is_unsat(option_constraints):
    solver = Solver()
    solver.add(pre_conditions)
    solver.add(option_constraints)
    return solver.check() == unsat

def is_sat(option_constraints):
    solver = Solver()
    solver.add(pre_conditions)
    solver.add(option_constraints)
    return solver.check() == sat

def is_accurate_list(option_constraints):
    return is_valid(Or(option_constraints)) and all([is_sat(c) for c in option_constraints])

def is_exception(x):
    return not x


if is_valid(rank(Mangoes) == 3): print('(A)')
if is_valid(rank(Kiwis) == 3): print('(B)')
if is_valid(rank(Plums) == 3): print('(C)')
if is_valid(rank(Pears) == 3): print('(D)')
if is_valid(rank(Watermelons) == 3): print('(E)')