# rville

## Current status

Working on "Rville scores 2024" sheet to tabulate scores.
In "Timetable annotated" sheet, working on how to find each player's
score entries in "Form Responses 1" and include into the scoresheet.
Rough plan: Add a column that finds the Index of a given player's
row within the Form Responses 1 tab, then use that Index column to
find the actual scores within the tab.

Rensselaerville Tennis Tournament Day 1 bracket generator

## How to use

Ensure you have CSVs containing timetables for the actual number
of men and women you have (or manually take an existing one for the
REVERSE number of men and women and switch it around and rename it).

If you don't, use src/main.py to generate what you need. You may need to
tweak things, possibly including constraint code, to make it work.

Use roster_to_randomized_namelist.py to generate namelist.txt, containing
randomized orderings of the men and women. First you'll need a roster.csv.

Then, run the csv_to_html.py script, following instructions therein.
Tweak HTML and CSS as necessary so that the output page, rendered in
a browser, can be saved to a good PDF. Also update the URL and QR Code
therein if necessary, though ideally we can keep reusing the original form
and spreadsheet.

The spreadsheet linked from that form, which is called "Rville scores 2024",
should do the rest.

## Original plan

I intend to build a program here that can generate a bracket for a mixed doubles "mixer" tournament, like this:

### Inputs

Number of male and female players
Number of courts
Session start times
List of "lunch" sessions of which each player should be "off" for at least one.
Optional stretch goal: Support individual extra requirements for the needs of specific players

### Output

Bracket listing team assignments for each court for each session, optimizing for variety of partners, opponents, and court assignments per person, minimal extensive consecutive assignments, etc.

This program will use Google's `ortools` package to optimize this.

## Dev stuff

(I haven't tried doing this in a while: I've mostly used replit to
handle dependencies, which is kind of separate)

Before doing anything with dependencies:

`python3 -m venv ~/venvs/rville`

(or substitute desired `venv` path)

This may require installing `python3` or the Python `venv` package via a package manager.

Then, activate the `venv`:

`source ~/venvs/rville/bin/activate`

When stopping: `deactivate` (no directory, no `source`, it's an executable in the `PATH`)

With `venv` activated, to add a new python dependency:

`pip3 install <<package name>>`

Then add that version of that package to `requirements.txt`.

To install dependencies in a new clone of this repository:

`pip3 install -r requirements.txt`

To check types:

Make sure `mypy` is installed:

`pip3 install mypy`

Then:

`python3 -m mypy src`
