import pytest
import main

data = [{
    'game': 'BAL @ TB',
    'id': 'L. Jackson',
    'prop': 'Pass Yds',
    'odds': 'o213.5 −115',
    'projection': '225.4'
}, {
    'game': 'BAL @ TB',
    'id': 'T. Brady',
    'prop': 'Pass Yds',
    'odds': 'o282.5 −115',
    'projection': '298.0'
}, {
    'game': 'BAL @ TB',
    'id': 'L. Jackson',
    'prop': 'Pass Completions',
    'odds': 'o19.5 −110',
    'projection': '20.2'
}, {
    'game': 'BAL @ TB',
    'id': 'T. Brady',
    'prop': 'Pass Completions',
    'odds': 'o25.5 −110',
    'projection': '28.8'
}, {
    'game': 'BAL @ TB',
    'id': 'L. Jackson',
    'prop': 'Pass Attempts',
    'odds': 'o29.5 +100',
    'projection': '33.2'
}, {
    'game': 'BAL @ TB',
    'id': 'T. Brady',
    'prop': 'Pass Attempts',
    'odds': 'o38.5 −130',
    'projection': '43.0'
}, {
    'game': 'BAL @ TB',
    'id': 'G. Edwards',
    'prop': 'Rush Yds',
    'odds': 'o44.5 −115',
    'projection': '55.7'
}, {
    'game': 'BAL @ TB',
    'id': 'L. Jackson',
    'prop': 'Rush Yds',
    'odds': 'o60.5 −115',
    'projection': '53.8'
}, {
    'game': 'BAL @ TB',
    'id': 'L. Fournette',
    'prop': 'Rush Yds',
    'odds': 'o50.5 −115',
    'projection': '50.6'
}, {
    'game': 'BAL @ TB',
    'id': 'C. Otton',
    'prop': 'Rec Yds',
    'odds': 'o29.5 −115',
    'projection': '24.6'
}, {
    'game': 'BAL @ TB',
    'id': 'C. Godwin',
    'prop': 'Rec Yds',
    'odds': 'o73.5 −115',
    'projection': '71.3'
}, {
    'game': 'BAL @ TB',
    'id': 'L. Fournette',
    'prop': 'Rec Yds',
    'odds': 'o29.5 −115',
    'projection': '33.1'
}, {
    'game': 'BAL @ TB',
    'id': 'M. Andrews',
    'prop': 'Rec Yds',
    'odds': 'o58.5 −115',
    'projection': '71.2'
}, {
    'game': 'BAL @ TB',
    'id': 'M. Evans',
    'prop': 'Rec Yds',
    'odds': 'o68.5 −115',
    'projection': '78.8'
}, {
    'game': 'BAL @ TB',
    'id': 'R. Bateman',
    'prop': 'Rec Yds',
    'odds': 'o47.5 −115',
    'projection': '36.8'
}, {
    'game': 'BAL @ TB',
    'id': 'C. Godwin',
    'prop': 'Receptions',
    'odds': 'o6.5 −140',
    'projection': '6.8'
}, {
    'game': 'BAL @ TB',
    'id': 'L. Fournette',
    'prop': 'Receptions',
    'odds': 'o4.5 +125',
    'projection': '5.0'
}, {
    'game': 'BAL @ TB',
    'id': 'M. Evans',
    'prop': 'Receptions',
    'odds': 'o4.5 −155',
    'projection': '5.4'
}, {
    'game': 'BAL @ TB',
    'id': 'R. White',
    'prop': 'Receptions',
    'odds': 'o2.5 +130',
    'projection': '2.6'
}, {
    'game': 'BAL @ TB',
    'id': 'L. Jackson',
    'prop': 'Rush Attempts',
    'odds': 'o9.5 −130',
    'projection': '9.2'
}, {
    'game': 'BAL @ TB',
    'id': 'L. Fournette',
    'prop': 'Rush Attempts',
    'odds': 'o13.5 +105',
    'projection': '13.7'
}]


class TestGrapg:

    def test_graph_builder(self):
        main.build_graphic(data, 21, 5)
