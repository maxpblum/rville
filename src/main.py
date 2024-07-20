import collections
import csv
import itertools
from ortools.sat.python import cp_model
from ortools.sat import cp_model_pb2

FinalAssignment = collections.namedtuple(
    'FinalAssignment', ['time_slot', 'court', 'team', 'man', 'woman'])


def assignment_name(time_slot, court, team, sex, player):
  return f'{time_slot}_{court}_{team}_{sex}_{player}'


def one_based_range(prefix: str, count: int) -> list[str]:
  return [f'{prefix}{n}' for n in range(1, count + 1)]


def solve(
    men_count: int, women_count: int, courts_count: int, time_slots: list[str]
) -> tuple[cp_model_pb2.CpSolverStatus, list[FinalAssignment]]:
  model = cp_model.CpModel()
  men = one_based_range(prefix='M', count=men_count)
  women = one_based_range(prefix='W', count=women_count)
  teams = ['T1', 'T2']
  courts = one_based_range(prefix='C', count=courts_count)

  assignments = {}
  for time_slot in time_slots:
    for court in courts:
      for team in teams:
        for man in men:
          name = assignment_name(time_slot, court, team, 'man', man)
          assignments[name] = model.NewBoolVar(name)
        for woman in women:
          name = assignment_name(time_slot, court, team, 'woman', woman)
          assignments[name] = model.NewBoolVar(name)

  # For a given court at a given time, there should either be no one or be exactly one man and one woman.
  for time_slot, court in itertools.product(time_slots, courts):
    team_one_men_assigned = [
        assignments[assignment_name(time_slot, court, 'T1', 'man', man)]
        for man in men
    ]
    team_one_women_assigned = [
        assignments[assignment_name(time_slot, court, 'T1', 'woman', woman)]
        for woman in women
    ]
    team_two_men_assigned = [
        assignments[assignment_name(time_slot, court, 'T2', 'man', man)]
        for man in men
    ]
    team_two_women_assigned = [
        assignments[assignment_name(time_slot, court, 'T2', 'woman', woman)]
        for woman in women
    ]
    model.add(sum(team_one_men_assigned) == sum(team_one_women_assigned))
    model.add(sum(team_two_men_assigned) == sum(team_two_women_assigned))
    model.add(sum(team_one_men_assigned) == sum(team_two_men_assigned))
    model.add(sum(team_one_men_assigned) <= 1)

  # For a given time slot, each man and woman should appear in at most one team.
  for time_slot in time_slots:
    for man in men:
      teams_assigned_to = []
      for court, team in itertools.product(courts, teams):
        teams_assigned_to.append(assignments[assignment_name(
            time_slot, court, team, 'man', man)])
        model.add(sum(teams_assigned_to) <= 1)
    for woman in women:
      teams_assigned_to = []
      for court, team in itertools.product(courts, teams):
        teams_assigned_to.append(assignments[assignment_name(
            time_slot, court, team, 'woman', woman)])
        model.add(sum(teams_assigned_to) <= 1)

  # A given player should have a lunch break, either the 12pm slot or the 1pm slot.
  for man in men:
    time_slots_assigned_to = []
    for time_slot, court, team in itertools.product(['12pm', '1pm'], courts,
                                                    teams):
      time_slots_assigned_to.append(assignments[assignment_name(
          time_slot, court, team, 'man', man)])
    model.add(sum(time_slots_assigned_to) <= 1)
  for woman in women:
    time_slots_assigned_to = []
    for time_slot, court, team in itertools.product(['12pm', '1pm'], courts,
                                                    teams):
      time_slots_assigned_to.append(assignments[assignment_name(
          time_slot, court, team, 'woman', woman)])
    model.add(sum(time_slots_assigned_to) <= 1)

  # Every player should play four or five matches.
  for man in men:
    time_slots_assigned_to = []
    for time_slot, court, team in itertools.product(time_slots, courts, teams):
      time_slots_assigned_to.append(assignments[assignment_name(
          time_slot, court, team, 'man', man)])
    model.add(sum(time_slots_assigned_to) >= 4)
    model.add(sum(time_slots_assigned_to) <= 5)
  for woman in women:
    time_slots_assigned_to = []
    for time_slot, court, team in itertools.product(time_slots, courts, teams):
      time_slots_assigned_to.append(assignments[assignment_name(
          time_slot, court, team, 'woman', woman)])
    model.add(sum(time_slots_assigned_to) >= 4)
    model.add(sum(time_slots_assigned_to) <= 5)

  solver = cp_model.CpSolver()
  status = solver.Solve(model)

  # No two players should appear in the same match more than once.
  for man, woman in itertools.product(men, women):
    joint_appearances = []
    # IMPLEMENT

  final_assignments: list[FinalAssignment] = []

  if status == cp_model.OPTIMAL:
    for time_slot, court, team, man, woman in itertools.product(
        time_slots, courts, teams, men, women):
      man_is_assigned = solver.Value(assignments[assignment_name(
          time_slot, court, team, 'man', man)])
      woman_is_assigned = solver.Value(assignments[assignment_name(
          time_slot, court, team, 'woman', woman)])
      if man_is_assigned and woman_is_assigned:
        final_assignments.append(
            FinalAssignment(time_slot, court, team, man, woman))

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
      w.writerow(['Time slot', 'Court', 'Team', 'Man', 'Woman'])
      for final_assignment in final_assignments:
        w.writerow(final_assignment)

  return status


def main():
  for men_count, women_count, courts_count in itertools.product(
      range(9, 12), range(9, 12), range(2, 6)):
    print(
        f'Solving for {men_count} men, {women_count} women, {courts_count} courts.'
    )
    status = generate_csv(
        filename=f'{men_count}men_{women_count}women_{courts_count}courts.csv',
        men_count=men_count,
        women_count=women_count,
        courts_count=courts_count,
        time_slots=['9am', '10am', '11am', '12pm', '1pm', '2pm', '3pm', '4pm'])
    if status == cp_model.OPTIMAL:
      print('Solution found.')
    else:
      print('No solution found.')


if __name__ == '__main__':
  main()
