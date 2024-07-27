import unittest
import main


def frozen_deep(xs, layers):
  if layers == 0:
    return frozenset(xs)
  return frozenset(frozen_deep(x, layers - 1) for x in xs)


class TestAllSubsetsOfSize(unittest.TestCase):

  def test_returns_expected_values(self):
    self.assertEqual(frozen_deep([[0], [1]], 1),
                     main.all_subsets_of_size(range(2), 1))
    self.assertEqual(frozen_deep([[0, 1], [0, 2], [1, 2]], 1),
                     main.all_subsets_of_size(range(3), 2))


class TestAllPairings(unittest.TestCase):

  def test_returns_expected_values(self):
    self.assertEqual(frozen_deep([[[0, 1]], [[1, 2]], [[0, 2]]], 2),
                     main.all_pairings(3, 1))
    self.assertEqual(
        frozen_deep([[[0, 1], [2, 3]], [[0, 2], [1, 3]], [[0, 3], [1, 2]]], 2),
        main.all_pairings(4, 2))


class TestAllTeamups(unittest.TestCase):

  def test_trivial_case(self):
    mens_team = frozenset([0, 1])
    womens_team = frozenset([0, 1])
    mens_full_courting = (mens_team,)
    womens_full_courting = (womens_team,)
    teamup = (mens_full_courting), (womens_full_courting)
    all_teamups_expected = frozenset([teamup])
    self.assertEqual(all_teamups_expected, main.all_teamups(2, 2, 1))


if __name__ == '__main__':
  unittest.main()
