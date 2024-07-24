import argparse
import collections
import csv
import itertools
import math
import random
import textwrap
from ortools.sat.python import cp_model
from ortools.sat import cp_model_pb2

Assignment = collections.namedtuple(
    "Assignment",
    [
        "time_slot",
        "court",
        "m_a",
        "m_b",
        "w_a",
        "w_b",
    ],
)


def one_based_range(prefix: str, count: int) -> list[str]:
    return [f"{prefix}{n}" for n in range(1, count + 1)]


def player_present(player: str, assignment: Assignment) -> bool:
    if player.startswith("M"):
        return assignment.m_a == player or assignment.m_b == player
    return assignment.w_a == player or assignment.w_b == player


def maybe_switch_women(a: Assignment) -> Assignment:
    new_w_a, new_w_b = (a.w_a, a.w_b) if random.random() < 0.5 else (a.w_b, a.w_a)
    return a._replace(w_a=new_w_a, w_b=new_w_b)


def solve(
    men_count: int,
    women_count: int,
    courts_count: int,
) -> tuple[cp_model_pb2.CpSolverStatus, list[Assignment]]:
    model = cp_model.CpModel()
    men = one_based_range(prefix="M", count=men_count)
    women = one_based_range(prefix="W", count=women_count)
    courts = one_based_range(prefix="C", count=courts_count)
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

    assignments: dict[Assignment, cp_model.IntVar] = {}

    # NEW STRATEGY TODO: Make an assignment represent an ENTIRE time slot and all of the people assigned to each court. Do this to leverage itertools.combinations to get rid of redundant assignments of the same grouping to different courts in the same time slot.
    for time_slot, court, (m_a, m_b), (w_a, w_b) in itertools.product(
        time_slots,
        courts,
        itertools.combinations(men, 2),
        itertools.combinations(women, 2),
    ):
        assignments[Assignment(time_slot, court, m_a, m_b, w_a, w_b)] = (
            model.NewBoolVar(f"{time_slot}_{court}_{m_a}_{m_b}_{w_a}_{w_b}")
        )

    # Every timeslot x court should have at most one assigned group.
    for time_slot, court in itertools.product(time_slots, courts):
        model.add(
            sum(
                v
                for k, v in assignments.items()
                if k.time_slot == time_slot and k.court == court
            )
            <= 1
        )

    # Players should have three or four matches.
    for p in men + women:
        model.add(sum(v for k, v in assignments.items() if player_present(p, k)) >= 3)
        model.add(sum(v for k, v in assignments.items() if player_present(p, k)) <= 4)

    # No two players should be in the same match twice.
    for p1, p2 in itertools.combinations(men + women, 2):
        model.add(
            sum(
                v
                for k, v in assignments.items()
                if player_present(p1, k) and player_present(p2, k)
            )
            <= 1
        )

    # Every player is in at most one match per time slot.
    for p, time_slot in itertools.product(men + women, time_slots):
        model.add(
            sum(
                v
                for k, v in assignments.items()
                if player_present(p, k) and k.time_slot == time_slot
            )
            <= 1
        )

    # No player should play three matches in a row.
    time_streaks = [time_slots[i : i + 3] for i in range(len(time_slots) - 2)]
    for p, streak in itertools.product(men + women, time_streaks):
        model.add(
            sum(
                v
                for k, v in assignments.items()
                if player_present(p, k) and k.time_slot in streak
            )
            < 3
        )

    # Pre-calculate the lateness score to apply for each court at a given time
    # slot.
    lateness_scores_per_time_slot = {time_slots[0]: 1}
    for time_slot in time_slots[1:]:
        prev_max_lateness_score = sum(
            courts_count * v for v in lateness_scores_per_time_slot.values()
        )
        lateness_scores_per_time_slot[time_slot] = prev_max_lateness_score + 1

    # Minimize the usage of later time slots.
    lateness_score = 0
    for (i, time_slot), (a_k, a_v) in itertools.product(
        enumerate(time_slots), assignments.items()
    ):
        if a_k.time_slot == time_slot:
            lateness_score += lateness_scores_per_time_slot[time_slot] * a_v
    model.minimize(lateness_score)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    final_assignments: list[Assignment] = (
        # Pair men and women randomly within each group of four.
        [maybe_switch_women(k) for k, v in assignments.items() if solver.Value(v)]
        if status == cp_model_pb2.OPTIMAL
        else []
    )

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
            w.writerow(["Time slot", "Court", "Man A", "Man B", "Woman A", "Woman B"])
            for final_assignment in final_assignments:
                w.writerow(final_assignment)

    return status


def string_to_two_int_tuple(in_str: str) -> tuple[int, int]:
    parts = in_str.split(",")
    if len(parts) != 2:
        raise ValueError(
            textwrap.dedent(
                """\
                Input must be two integers separated by one comma and no empty
                space.
                """
            )
        )
    return int(parts[0]), int(parts[1])


def main():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(
            """\
            Output rville tennis tournament day 1 brackets for various numbers
            of men, women, and courts."""
        ),
    )
    parser.add_argument(
        "--min_max_men_count", type=string_to_two_int_tuple, required=True
    )
    parser.add_argument(
        "--min_max_women_count", type=string_to_two_int_tuple, required=True
    )
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
            filename=f"{men_count}men_{women_count}women_{courts_count}courts.csv",
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
