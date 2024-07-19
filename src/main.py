import itertools
from ortools.sat.python import cp_model


def assignment_name(time_slot, court, team, sex, player):
  return f'{time_slot}_{court}_{team}_{sex}_{player}'


def main():
  model = cp_model.CpModel()
  men = ['M1', 'M2', 'M3', 'M4']
  women = ['W1', 'W2', 'W3', 'W4']
  teams = ['T1', 'T2']
  courts = ['C1', 'C2']
  time_slots = ['9am', '10am', '11am', '12pm', '1pm', '2pm', '3pm']

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

  # For a given team at a given court at a given time slot, there should be exactly one man and one woman.
  for time_slot, court, team in itertools.product(time_slots, courts, teams):
    men_assigned = []
    women_assigned = []
    for man in men:
      men_assigned.append(assignments[assignment_name(time_slot, court, team,
                                                      'man', man)])
    for woman in women:
      women_assigned.append(assignments[assignment_name(
          time_slot, court, team, 'woman', woman)])
    model.add(sum(men_assigned) == 1)
    model.add(sum(women_assigned) == 1)

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

  solver = cp_model.CpSolver()
  status = solver.Solve(model)

  print(f'Status: {status}')

  for time_slot, court, team, man, woman in itertools.product(
      time_slots, courts, teams, men, women):
    man_is_assigned = solver.Value(assignments[assignment_name(
        time_slot, court, team, 'man', man)])
    woman_is_assigned = solver.Value(assignments[assignment_name(
        time_slot, court, team, 'woman', woman)])
    if man_is_assigned and woman_is_assigned:
      print(
          f'Time slot: {time_slot}, Court: {court}, Team: {team}, Man: {man}, Woman: {woman}'
      )


if __name__ == '__main__':
  main()
