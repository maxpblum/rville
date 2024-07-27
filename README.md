# rville

Rensselaerville Tennis Tournament Day 1 bracket generator

I intend to build a program here that can generate a bracket for a mixed doubles "mixer" tournament, like this:

## Inputs

Number of male and female players
Number of courts
Session start times
List of "lunch" sessions of which each player should be "off" for at least one.
Optional stretch goal: Support individual extra requirements for the needs of specific players

## Output

Bracket listing team assignments for each court for each session, optimizing for variety of partners, opponents, and court assignments per person, minimal extensive consecutive assignments, etc.

This program will use Google's `ortools` package to optimize this.

## Dev stuff

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
