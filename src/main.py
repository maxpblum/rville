import argparse
import collections
import csv
import itertools
import math
import random
import textwrap
from typing import Literal

from ortools.sat.python import cp_model
from ortools.sat import cp_model_pb2

# This feature currently seems to lead to infeasibility.
NO_REPEAT_TOWN_COURT = False

# We'd never really go to 6pm, but these are only theoretical time slots.
TimeSlot = Literal[
    "9am",
    "10am",
    "11am",
    "12pm",
    "1pm",
    "2pm",
    "3pm",
    "4pm",
    "5pm",
    "6pm",
]
ALL_TIME_SLOTS: list[TimeSlot] = [
    "9am",
    "10am",
    "11am",
    "12pm",
    "1pm",
    "2pm",
    "3pm",
    "4pm",
    "5pm",
    "6pm",
]

Gender = Literal["M", "W"]
ALL_GENDERS: list[Gender] = ["M", "W"]

Player = collections.namedtuple('Player', ['gender', 'id'])

Assignment = collections.namedtuple(
    'Assignment', ['time_slot', 'men', 'women'] +
    (['is_town_court'] if NO_REPEAT_TOWN_COURT else []),
    defaults=([False] if NO_REPEAT_TOWN_COURT else []))


def player_present(a: Assignment, p: Player):
    return p.id in (a.men if p.gender == "M" else a.women)


AssignmentVar = collections.namedtuple('AssignmentVar', ['a', 'v'])


def solve(
    men_count: int,
    women_count: int,
    courts_count: int,
    matches_count: int,
    accommodate_blampos: bool,
) -> tuple[cp_model_pb2.CpSolverStatus, list[Assignment]]:
    model = cp_model.CpModel()

    men = [Player(gender="M", id=id) for id in range(1, men_count + 1)]
    max_player = men[3]
    max_time_slots = ['11am', '12pm', '3pm']
    women = [Player(gender="W", id=id) for id in range(1, women_count + 1)]
    gigi_player = women[5]
    gigi_time_slots = ['9am', '10am', '2pm']
    all_players: list[Player] = men + women

    # A mapping from time slot to number of courts.
    settings: dict[TimeSlot, int] = collections.Counter()
    for time_slot in ALL_TIME_SLOTS:
        settings.update({time_slot: min(matches_count, courts_count)})
        matches_count -= settings[time_slot]
        if matches_count == 0:
            break

    time_slots = list(settings.keys())

    assignments: list[AssignmentVar] = []

    for time_slot, men_pair, women_pair in itertools.product(
            time_slots,
            itertools.combinations(men, 2),
            itertools.combinations(women, 2),
    ):
        # Special cases to help Max and Gigi get parenting done.
        if accommodate_blampos and max_player in men_pair and time_slot not in max_time_slots:
            continue
        if accommodate_blampos and gigi_player in women_pair and time_slot not in gigi_time_slots:
            continue

        assignment = Assignment(time_slot=time_slot,
                                men=(men_pair[0].id, men_pair[1].id),
                                women=(women_pair[0].id, women_pair[1].id))
        var = model.NewBoolVar(repr(assignment))
        assignments.append(AssignmentVar(a=assignment, v=var))
        if NO_REPEAT_TOWN_COURT:
            assignment = assignment._replace(is_town_court=True)
            var = model.NewBoolVar(repr(assignment))
            assignments.append(AssignmentVar(a=assignment, v=var))

    # Every court should have at most one match per time slot.
    for (time_slot, ts_courts_count) in settings.items():
        model.add(
            sum(a.v for a in assignments
                if a.a.time_slot == time_slot) <= ts_courts_count)

    # If town court is bad, there should be <= 1 town court
    # match per time slot, no player should play on it more than
    # twice.
    if NO_REPEAT_TOWN_COURT:
        for time_slot in time_slots:
            model.add(
                sum(a.v for a in assignments
                    if a.a.is_town_court and a.a.time_slot == time_slot) <= 1)
        for p in all_players:
            model.add(
                sum(a.v for a in assignments if player_present(a.a, p)) <= 2)

    # Players should have three or four matches.
    for p in all_players:
        model.add(sum(a.v for a in assignments if player_present(a.a, p)) >= 3)
        model.add(sum(a.v for a in assignments if player_present(a.a, p)) <= 4)

    # No two players should be in the same match twice.
    for pa, pb in itertools.combinations(all_players, 2):
        model.add(
            sum(a.v for a in assignments
                if player_present(a.a, pa) and player_present(a.a, pb)) <= 1)

    # Every player is in at most one match per time slot.
    for p, time_slot in itertools.product(all_players, time_slots):
        model.add(
            sum(a.v for a in assignments
                if player_present(a.a, p) and a.a.time_slot == time_slot) <= 1)

    # No player should play three matches in a row.
    time_streaks = [time_slots[i:i + 3] for i in range(len(time_slots) - 2)]
    for p, streak in itertools.product(all_players, time_streaks):
        model.add(
            sum(a.v for a in assignments
                if player_present(a.a, p) and a.a.time_slot in streak) < 3)

    print('Solving')
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(f'Status: {solver.StatusName(status)}')

    final_assignments: list[Assignment] = (
        [a.a for a in assignments
         if solver.Value(a.v)] if status == cp_model_pb2.OPTIMAL else [])

    return status, final_assignments


def generate_csv(
    filename: str,
    men_count: int,
    women_count: int,
    courts_count: int,
    matches_count: int,
    accommodate_blampos: bool,
) -> cp_model_pb2.CpSolverStatus:
    status, final_assignments = solve(
        men_count=men_count,
        women_count=women_count,
        courts_count=courts_count,
        matches_count=matches_count,
        accommodate_blampos=accommodate_blampos,
    )

    # Randomize court assignments within each time slot.
    grouped_by_time_slot = collections.defaultdict(list)
    for a in final_assignments:
        grouped_by_time_slot[a.time_slot].append(a)
    for assignments in grouped_by_time_slot.values():
        if NO_REPEAT_TOWN_COURT:
            initial_assignments = [a for a in assignments if a.is_town_court]
            remaining = [a for a in assignments if not a.is_town_court]
        else:
            initial_assignments = []
            remaining = assignments
        random.shuffle(remaining)
        assignments = initial_assignments + remaining
    shuffled_assignments: list[tuple[Assignment, int]] = [
        (a, court) for assignments in grouped_by_time_slot.values()
        for (a, court) in zip(assignments, range(1, courts_count + 1))
    ]

    if status == cp_model.OPTIMAL:
        with open(filename, "w") as f:
            w = csv.writer(f)
            w.writerow(
                ["Time slot", "Court", "Man A", "Woman A", "Man B", "Woman B"])
            for fa, court in shuffled_assignments:
                # Randomize team pairings within each quad.
                men = list(fa.men)
                women = list(fa.women)
                random.shuffle(men)
                random.shuffle(women)

                w.writerow(
                    (fa.time_slot, court, men[0], women[0], men[1], women[1]))

    return status


def string_to_two_int_tuple(in_str: str) -> tuple[int, int]:
    parts = in_str.split(",")
    if len(parts) != 2:
        raise ValueError(
            textwrap.dedent("""\
                Input must be two integers separated by one comma and no empty
                space.
                """))
    return int(parts[0]), int(parts[1])


def get_min_matches_to_try(men_count: int, women_count: int) -> int:
    return 3 * math.ceil(max(men_count, women_count) / 2)


def main():
    parser = argparse.ArgumentParser(description=textwrap.dedent("""\
            Output rville tennis tournament day 1 brackets for various numbers
            of men, women, and courts."""), )
    parser.add_argument("--min_max_men_count",
                        type=string_to_two_int_tuple,
                        required=True)
    parser.add_argument("--min_max_women_count",
                        type=string_to_two_int_tuple,
                        required=True)
    parser.add_argument("--courts_count", type=int, required=True)
    parser.add_argument("--accommodate_blampos", type=bool, default=False)

    parsed = parser.parse_args()

    courts_count: int = parsed.courts_count
    min_max_men_count: tuple[int, int] = parsed.min_max_men_count
    min_max_women_count: tuple[int, int] = parsed.min_max_women_count
    accommodate_blampos: bool = parsed.accommodate_blampos

    if accommodate_blampos:
        print('Accommodating Blampos')

    combinations_tried: set[tuple[int, int]] = set()

    for men_count, women_count in itertools.product(
            range(min_max_men_count[0], min_max_men_count[1] + 1),
            range(min_max_women_count[0], min_max_women_count[1] + 1),
    ):
        sorted_order = (men_count,
                        women_count) if men_count <= women_count else (
                            women_count, men_count)
        if sorted_order in combinations_tried:
            # Example: If we already calculated for 7 men and 4 women, skip
            # for 4 men and 7 women because we can just switch the previous
            # results.
            continue
        combinations_tried.add(sorted_order)

        if sorted_order[1] - sorted_order[0] > 3:
            # If the number of men and women varies by more than 3, it often or
            # always seems to make solutions infeasible. Let's cross this bridge
            # when we come to it: If we have a combination of people for whom
            # the result is infeasible, try relaxing some constraints.
            continue

        print(
            f"Solving for {men_count} men, {women_count} women, {courts_count} courts."
        )
        min_matches_to_try = get_min_matches_to_try(men_count, women_count)
        solution_found = False
        for matches_count in range(min_matches_to_try,
                                   len(ALL_TIME_SLOTS) * courts_count + 1):
            print(f"Trying {matches_count} matches.")

            blampos_name_part = '_helpingblampos' if accommodate_blampos else ''

            status = generate_csv(
                filename=
                f"{men_count}men_{women_count}women_{courts_count}courts{blampos_name_part}.csv",
                men_count=men_count,
                women_count=women_count,
                courts_count=courts_count,
                matches_count=matches_count,
                accommodate_blampos=accommodate_blampos,
            )
            if status == cp_model.OPTIMAL:
                solution_found = True
                break
        print(f"Solution found: {solution_found}")


if __name__ == "__main__":
    main()
