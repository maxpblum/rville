import collections
import csv
import itertools
from ortools.sat.python import cp_model
from ortools.sat import cp_model_pb2

Assignment = collections.namedtuple(
    'Assignment',
    [
        'time_slot',
        'court',
        'm_a',
        'm_b',
        'w_a',
        'w_b',
    ],
)


def one_based_range(prefix: str, count: int) -> list[str]:
  return [f'{prefix}{n}' for n in range(1, count + 1)]


def player_present(player: str, assignment: Assignment) -> bool:
  if player.startswith('M'):
    return assignment.m_a == player or assignment.m_b == player
  return assignment.w_a == player or assignment.w_b == player


def solve(
    men_count: int, women_count: int, courts_count: int, time_slots: list[str]
) -> tuple[cp_model_pb2.CpSolverStatus, list[Assignment]]:
  model = cp_model.CpModel()
  men = one_based_range(prefix='M', count=men_count)
  women = one_based_range(prefix='W', count=women_count)
  courts = one_based_range(prefix='C', count=courts_count)

  assignments: dict[Assignment, cp_model.IntVar] = {}

  for time_slot, court, (m_a, m_b), (w_a, w_b) in itertools.product(time_slots, courts, itertools.combinations(men, 2), itertools.combinations(women, 2)):
    assignments[Assignment(time_slot, court, m_a, m_b, w_a, w_b)] = model.NewBoolVar(f'{time_slot}_{court}_{m_a}_{m_b}_{w_a}_{w_b}')

  # Every timeslot x court should have at most one assigned group.
  for time_slot, court in itertools.product(time_slots, courts):
    model.add(sum(v for k, v in assignments.items() if k.time_slot == time_slot and k.court == court) <= 1)

  # Every player should have between three and four matches.
  for p in men + women:
    model.add(sum(v for k, v in assignments.items() if player_present(p, k)) >= 3)
    model.add(sum(v for k, v in assignments.items() if player_present(p, k)) <= 4)

  # No two players should be in the same match twice.
  for p1, p2 in itertools.combinations(men + women, 2):
    model.add(sum(v for k, v in assignments.items() if player_present(p1, k) and player_present(p2, k)) <= 1)

  # Every player should have a lunch break.
  # for p in men + women:
    # model.add(sum(v for k, v in assignments.items() if player_present(p, k) and k.time_slot in ['12pm', '1pm']) <= 1)

  # Every player is in at most one match per time slot.
  for p, time_slot in itertools.product(men + women, time_slots):
    model.add(sum(v for k, v in assignments.items() if player_present(p, k) and k.time_slot == time_slot) <= 1)

  # No player should play three matches in a row.
  time_streaks = [time_slots[i:i + 3] for i in range(len(time_slots) - 2)]
  for p, streak in itertools.product(men + women, time_streaks):
    model.add(sum(v for k, v in assignments.items() if player_present(p, k) and k.time_slot in streak) < 3)

  solver = cp_model.CpSolver()
  status = solver.Solve(model)

  final_assignments: list[Assignment] = [k for k, v in assignments.items() if solver.Value(v)] if status == cp_model_pb2.OPTIMAL else []

  return status, final_assignments


def generate_csv(filename: str, men_count: int, women_count: int,
                 courts_count: int,
                 time_slots: list[str]) -> cp_model_pb2.CpSolverStatus:
  status, final_assignments = solve(men_count=men_count,
                                    women_count=women_count,
                                    courts_count=courts_count,
                                    time_slots=time_slots)
  if status == cp_model.OPTIMAL:
    with open(filename, 'w') as f:
      w = csv.writer(f)
      w.writerow(['Time slot', 'Court', 'Man A', 'Man B', 'Woman A', 'Woman B'])
      for final_assignment in final_assignments:
        w.writerow(final_assignment)

  return status


def main():
  for men_count, women_count, courts_count in itertools.product(
      range(14, 15), range(14, 15), range(3, 4)):
    print(
        f'Solving for {men_count} men, {women_count} women, {courts_count} courts.'
    )
    status = generate_csv(
        filename=f'{men_count}men_{women_count}women_{courts_count}courts.csv',
        men_count=men_count,
        women_count=women_count,
        courts_count=courts_count,
        time_slots=['9am', '10am', '11am', '12pm', '1pm', '2pm', '3pm'])
    if status == cp_model.OPTIMAL:
      print('Solution found.')
    else:
      print('No solution found.')


if __name__ == '__main__':
  main()
