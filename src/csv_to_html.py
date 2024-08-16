import csv
import dataclasses
import textwrap


@dataclasses.dataclass
class Team:
  man: int
  woman: int

  def __str__(self):
    return f'M{self.man}\nW{self.woman}'


@dataclasses.dataclass
class OneTeamAcrossCourts:
  teams: list[Team]


@dataclasses.dataclass
class OneTimeSlotAcrossCourts:
  time_slot: str
  teams_across_courts: list[OneTeamAcrossCourts]


@dataclasses.dataclass
class TimeSlotsAcrossCourts:
  time_slots: list[OneTimeSlotAcrossCourts]


def make_td(team) -> str:
  return f'<td>{team}</td>'


def make_team_tds(one_team_across_courts: OneTeamAcrossCourts) -> str:
  return ''.join(make_td(team) for team in one_team_across_courts.teams)


def make_time_slot_rows(
    one_time_slot_across_courts: OneTimeSlotAcrossCourts) -> str:
  return textwrap.dedent(f'''\
      <tr>
        <td rowspan="2">{one_time_slot_across_courts.time_slot}</td>
        {make_team_tds(one_time_slot_across_courts.teams_across_courts[0])}
      </tr>
      <tr>
        {make_team_tds(one_time_slot_across_courts.teams_across_courts[1])}
      </tr>''')


def make_all_time_slot_rows(time_slots_across_courts: TimeSlotsAcrossCourts):
  return '\n'.join(
      make_time_slot_rows(t) for t in time_slots_across_courts.time_slots)


if __name__ == '__main__':
  time_slots = TimeSlotsAcrossCourts([])
  with open('12men_13women_3courts.csv', 'r') as csvfile:
    reader = iter(csv.reader(csvfile))

    # Throw out the header row
    next(reader)

    for row in reader:
      if len(time_slots.time_slots
             ) == 0 or time_slots.time_slots[-1].time_slot != row[0]:
        time_slot = OneTimeSlotAcrossCourts(
            row[0], [OneTeamAcrossCourts([]),
                     OneTeamAcrossCourts([])])
        time_slots.time_slots.append(time_slot)
        time_slot = time_slots.time_slots[-1]
      else:
        time_slot = time_slots.time_slots[-1]
      court_idx = int(row[1])
      time_slot.teams_across_courts[0].teams.append(
          Team(int(row[2]), int(row[3])))
      time_slot.teams_across_courts[1].teams.append(
          Team(int(row[4]), int(row[5])))

  named_courts = [
      f'Court {i}' for i in range(
          1,
          len(time_slots.time_slots[0].teams_across_courts[0].teams) + 1)
  ]
  court_ths = '\n'.join(f'<th scope="col">{c}</th>' for c in named_courts)
  style = '''\
* { font-family: sans-serif; }
table, th, td { border: solid; padding: 1em; }
table { float: left; margin-right: 1em; }
legend { float: right; }
#formlink { font-size: 0.8em; }
'''

  with open('table.html', 'w') as f:
    f.write(
        textwrap.dedent(f'''\
          <style>
          {style}
          </style>
          <table>
          <tr>
            <th scope="col">Time slot</td>
            {court_ths}
          </tr>
          {make_all_time_slot_rows(time_slots)}
          </table>
          <div class="legend">
          <h1>Legend</h1>
          Court 1 = Town court<br/>
          Court 2 = Rooney court<br/>
          Court 3 = Douglas court<br/>
          M1 = Max Blum-Campo<br/>
          M2 = Blax Mum-Campo<br/>
          M3 = Cax Mum-Blampo<br/>
          <h1>Scores</h1>
          Please write your scores here and then submit them
          online at
          <span id="formlink">https://forms.gle/T6JKqzox57oiEyxL7</span><br/>
          Match 1 games WON <input value="   "></input><br/>
          Match 1 games LOST <input value="   "></input><br/>
          Match 2 games WON <input value="   "></input><br/>
          Match 2 games LOST <input value="   "></input><br/>
          Match 3 games WON <input value="   "></input><br/>
          Match 3 games WON <input value="   "></input><br/>
          Match 4 games LOST <input value="   "></input><br/>
          Match 4 games LOST <input value="   "></input><br/>
          </div>
          '''))
