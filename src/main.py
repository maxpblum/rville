import argparse
import json
from collections.abc import Iterable, Sequence
import copy
import csv
from dataclasses import dataclass
import itertools
import math
import random
import textwrap
from typing import TypeVar
from ortools.sat.python import cp_model
from ortools.sat import cp_model_pb2

# PLANNING TO ABANDON MOST OF THE CURRENT APPROACH.
# I made the strange decision a couple of days ago to try switching to
# a model where each boolvar represents an entire *set of court assignments*
# for a time slot across all courts. This opened the door to certain optimizations,
# letting me *skip* making boolvars for combinations that make no sense, but
# it also makes this whole thing monstrously hard to think about, and the sheer
# number of boolvars seems likely to become an issue. The final straw was realizing
# that I would need to take each boolvar and duplicate many times it to represent
# "omitting" some of the matches from it.

T = TypeVar('T')


def all_subsets_of_size(superset: Iterable[T],
                        size: int) -> frozenset[frozenset[T]]:
    return frozenset(
        frozenset(c) for c in itertools.combinations(superset, size))


def all_pairings(players: int,
                 courts: int) -> frozenset[frozenset[frozenset[int]]]:
    # All sets of players that can fill courts with two players per court,
    # e.g. all sets of 6 players if there are 3 courts.
    all_full_courtings: frozenset[frozenset[int]] = all_subsets_of_size(
        range(players), 2 * courts)
    pairings: set[frozenset[frozenset[int]]] = set()
    for full_courting in all_full_courtings:
        for ordering in itertools.permutations(full_courting, 2 * courts):
            pairs: set[frozenset[int]] = set()
            for i in range(0, len(ordering), 2):
                pairs.add(frozenset(ordering[i:i + 2]))
            pairings.add(frozenset(pairs))
    return frozenset(pairings)


# One "teamup" is a tuple consisting of two smaller tuples, the first of which
# contains a pair of men for each court (each pair is a frozenset of two ints),
# the second of which contains a pair of women for each court.
def all_teamups(
    men: int, women: int, courts: int
) -> frozenset[tuple[Sequence[frozenset[int]], Sequence[frozenset[int]]]]:
    teamups: set[tuple[Sequence[frozenset[int]], Sequence[frozenset[int]]]] = set()
    all_men_pairings = all_pairings(men, courts)
    all_women_pairings = all_pairings(women, courts)
    for mp, wp in itertools.product(all_men_pairings, all_women_pairings):
        sorted_mp = tuple(sorted(mp))
        for w_ordering in itertools.permutations(wp, courts):
            # Need a way to represent having only some courts occupied in a time slot
            teamups.add((sorted_mp, w_ordering))
    return frozenset(teamups)


def solve(
    men_count: int,
    women_count: int,
    courts_count: int,
) -> tuple[cp_model_pb2.CpSolverStatus, list[Assignment]]:
    model = cp_model.CpModel()
    # We'd never really go to 6pm, but these are only theoretical time slots.
    time_slots = [
        "9am",
        "10am",
        "11am",
        "12pm",
        "1pm",
        "2pm",
        "3pm",
        "4pm",
        # "5pm",
        # "6pm",
    ]

    assignments = {}
    for time_slot, teamup in itertools.product(time_slots, all_teamups(men_count, women_count, courts_count)):
        assignments[(time_slot, teamup)] = model.NewBoolVar(f"{(time_slot, teamup)}")

    # Every timeslot should have at most one assignment.
    for time_slot in time_slots:
        model.add(sum(v for k, v in assignments.items() if k[0] == time_slot) <= 1)

    # Players should have three or four matches.

    # No two players should be in the same match twice.

    # Every player is in at most one match per time slot.

    # No player should play three matches in a row.
    time_streaks = [time_slots[i:i + 3] for i in range(len(time_slots) - 2)]
    for p, streak in itertools.product(men + women, time_streaks):
        pass

    # Pre-calculate the lateness score to apply for each court at a given time
    # slot.
    lateness_scores_per_time_slot = {time_slots[0]: 1}
    for time_slot in time_slots[1:]:
        prev_max_lateness_score = sum(
            courts_count * v for v in lateness_scores_per_time_slot.values())
        lateness_scores_per_time_slot[time_slot] = prev_max_lateness_score + 1

    # Minimize the usage of later time slots.
    lateness_score = 0
    for (i, time_slot), (a_k,
                         a_v) in itertools.product(enumerate(time_slots),
                                                   assignments.items()):
        pass
    model.minimize(lateness_score)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    final_assignments: list[Assignment] = []
    # Pair men and women randomly within each group of four.
    # TODO: Randomize court assignments, too.
    # [
    #     maybe_switch_women(k) for k, v in assignments.items()
    #     if solver.Value(v)
    # ] if status == cp_model_pb2.OPTIMAL else [])

    return status, final_assignments


def generate_csv(
    filename: str,
    men_count: int,
    women_count: int,
    courts_count: int,
) -> cp_model_pb2.CpSolverStatus:
    status, final_assignments = solve(
        men_count=men_count,
        women_count=women_count,
        courts_count=courts_count,
    )
    if status == cp_model.OPTIMAL:
        with open(filename, "w") as f:
            w = csv.writer(f)
            w.writerow(
                ["Time slot", "Court", "Man A", "Man B", "Woman A", "Woman B"])
            for final_assignment in final_assignments:
                raise NotImplementedError()
                # w.writerow(final_assignment)

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

    parsed = parser.parse_args()

    courts_count: int = parsed.courts_count
    min_max_men_count: tuple[int, int] = parsed.min_max_men_count
    min_max_women_count: tuple[int, int] = parsed.min_max_women_count

    for men_count, women_count in itertools.product(
            range(min_max_men_count[0], min_max_men_count[1] + 1),
            range(min_max_women_count[0], min_max_women_count[1] + 1),
    ):
        print(
            f"Solving for {men_count} men, {women_count} women, {courts_count} courts."
        )
        status = generate_csv(
            filename=
            f"{men_count}men_{women_count}women_{courts_count}courts.csv",
            men_count=men_count,
            women_count=women_count,
            courts_count=courts_count,
        )
        if status == cp_model.OPTIMAL:
            print("Solution found.")
        else:
            print("No solution found.")


if __name__ == "__main__":
    main()
