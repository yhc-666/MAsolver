from z3 import *

Book_sort, (Green, Blue, White, Purple, Yellow) = EnumSort('Book', ['Green', 'Blue', 'White', 'Purple', 'Yellow'])
Position_sort = IntSort()
Position = [1, 2, 3, 4, 5]
Book = [Green, Blue, White, Purple, Yellow]
pos = Function('pos', Book_sort, Position_sort)

pre_conditions = []
pre_conditions.append(Distinct([pos(b) for b in Book]))
pre_conditions.append(pos(Blue) > pos(Yellow))
pre_conditions.append(pos(White) < pos(Yellow))
pre_conditions.append(pos(Blue) == 4)
pre_conditions.append(pos(Purple) == 2)
B0 = Const('B0', Book_sort)
pre_conditions.append(ForAll([B0], And(1 <= pos(B0), pos(B0) <= 5)))

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


if is_valid(pos(Green) == 2): print('(A)')
if is_valid(pos(Blue) == 2): print('(B)')
if is_valid(pos(White) == 2): print('(C)')
if is_valid(pos(Purple) == 2): print('(D)')
if is_valid(pos(Yellow) == 2): print('(E)')