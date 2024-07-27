import argparse
import collections
from collections.abc import Iterable
import csv
from dataclasses import dataclass
import itertools
import math
import random
import textwrap
from typing import Literal

from ortools.sat.python import cp_model
from ortools.sat import cp_model_pb2

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


@dataclass(frozen=True)
class Player:
    gender: Gender
    id: int


def make_pair(p1: Player, p2: Player) -> frozenset[int]:
    return frozenset([p1.id, p2.id])


@dataclass(frozen=True)
class Assignment:
    time_slot: TimeSlot
    court: int
    men: frozenset[int]
    women: frozenset[int]

    def player_present(self, p: Player):
        return p.id in (self.men if p.gender == "M" else self.women)


@dataclass(frozen=True)
class AssignmentVar:
    a: Assignment
    v: cp_model.IntVar


def solve(
    men_count: int,
    women_count: int,
    courts_count: int,
    matches_count: int,
) -> tuple[cp_model_pb2.CpSolverStatus, list[Assignment]]:
    model = cp_model.CpModel()

    men = [Player(gender="M", id=id) for id in range(1, men_count + 1)]
    women = [Player(gender="W", id=id) for id in range(1, women_count + 1)]
    all_players: list[Player] = men + women
    courts = range(1, courts_count + 1)

    # A mapping from time slot to list of courts.
    settings: dict[TimeSlot, list[int]] = collections.defaultdict(list)
    for _, (time_slot, court) in zip(range(matches_count),
                                     itertools.product(ALL_TIME_SLOTS,
                                                       courts)):
        settings[time_slot].append(court)
    time_slots = list(settings.keys())

    def iter_settings() -> Iterable[tuple[TimeSlot, int]]:
        for time_slot, courts in settings.items():
            for court in courts:
                yield time_slot, court

    assignments: list[AssignmentVar] = []

    for (time_slot, court), men_pair, women_pair in itertools.product(
            iter_settings(),
            itertools.combinations(men, 2),
            itertools.combinations(women, 2),
    ):
        assignment = Assignment(time_slot, court, make_pair(*men_pair),
                                make_pair(*women_pair))
        var = model.NewBoolVar(repr(assignment))
        assignments.append(AssignmentVar(a=assignment, v=var))

    # Every timeslot x court should have exactly one assigned group.
    for time_slot, court in iter_settings():
        model.add(
            sum(a.v for a in assignments
                if a.a.time_slot == time_slot and a.a.court == court) == 1)

    # Players should have three or four matches.
    for p in men + women:
        player_match_count = sum(a.v for a in assignments
                                 if a.a.player_present(p))
        model.add(player_match_count >= 3)
        model.add(player_match_count <= 4)

    # No two players should be in the same match twice.

    # Every player is in at most one match per time slot.
    for p, time_slot in itertools.product(all_players, time_slots):
        model.add(
            sum(a.v for a in assignments
                if a.a.player_present(p) and a.a.time_slot == time_slot) <= 1)

    # No player should play three matches in a row.
    # time_streaks = [time_slots[i : i + 3] for i in range(len(time_slots) - 2)]
    # for p, streak in itertools.product(men + women, time_streaks):
    #  pass

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

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
) -> cp_model_pb2.CpSolverStatus:
    status, final_assignments = solve(
        men_count=men_count,
        women_count=women_count,
        courts_count=courts_count,
        matches_count=matches_count,
    )
    if status == cp_model.OPTIMAL:
        with open(filename, "w") as f:
            w = csv.writer(f)
            w.writerow(
                ["Time slot", "Court", "Man A", "Man B", "Woman A", "Woman B"])
            for fa in final_assignments:
                men = list(fa.men)
                women = list(fa.women)
                random.shuffle(men)
                random.shuffle(women)
                w.writerow((fa.time_slot, fa.court, men[0], men[1], women[0],
                            women[1]))

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
        min_matches_to_try = get_min_matches_to_try(men_count, women_count)
        solution_found = False
        for matches_count in range(min_matches_to_try, min_matches_to_try * 5):
            print(f"Trying {matches_count} matches.")
            status = generate_csv(
                filename=
                f"{men_count}men_{women_count}women_{courts_count}courts.csv",
                men_count=men_count,
                women_count=women_count,
                courts_count=courts_count,
                matches_count=matches_count,
            )
            if status == cp_model.OPTIMAL:
                solution_found = True
                break
        print(f"Solution found: {solution_found}")


if __name__ == "__main__":
    main()
