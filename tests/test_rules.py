import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rules import get_combined_recommendation, lash_mapping_rules


def test_same_shapes_returns_single_recommendation():
    rec = get_combined_recommendation('almond', 'almond')
    assert rec == lash_mapping_rules['almond']


def test_different_shapes_merged():
    rec = get_combined_recommendation('almond', 'round')
    assert rec['style'] == 'Beliebig / Cat / Squirrel'
    assert rec['mapping'] == 'Left: Individuell, Right: Außen betont'
    assert rec['curl'] == 'C / CC / C / D'
