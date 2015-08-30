import datetime as dt
import json
import mock
import unittest

import app as web_app
import lastfm


def load_fake_data():
    with open('fixtures/chart.json', 'r') as f:
        fake_chart_resp = json.loads(f.read())
    with open('fixtures/albums.json', 'r') as f:
        fake_albums_resp = json.loads(f.read())
    charts = []
    for chart in fake_chart_resp['weeklychartlist']['chart']:
        charts.append({
            'from': chart['from'],
            'to': chart['to'],
            'from_date': lastfm.timestamp_to_date(chart['from']),
            'to_date': lastfm.timestamp_to_date(chart['to']),
        })
    return {
        'fake_chart_resp': fake_chart_resp,
        'fake_albums_resp': fake_albums_resp,
        'charts': charts,
    }


class LastFMTestCase(unittest.TestCase):

    def setUp(self):
        data = load_fake_data()
        self.fake_chart_resp = data['fake_chart_resp']
        self.fake_albums_resp = data['fake_albums_resp']
        self.charts = data['charts']

    @mock.patch('lastfm.requests.get')
    def test_get_charts(self, mock_get):
        mock_resp = mock.Mock()
        mock_resp.json.return_value = self.fake_chart_resp
        mock_get.return_value = mock_resp
        charts = lastfm.chart_list('J_Roche')
        self.assertGreater(len(charts), 50)

    @mock.patch('lastfm.requests.get')
    @mock.patch('lastfm.chart_list')
    def test_get_albums_load_charts(self, mock_chart, mock_get):
        mock_resp = mock.Mock()
        mock_resp.json.return_value = self.fake_albums_resp
        mock_get.return_value = mock_resp
        mock_chart.return_value = self.charts
        albums = lastfm.top_albums('J_Roche', dt.date(2015, 7, 1))

        mock_chart.assert_called_once_with('J_Roche')
        self.assertEqual(len(albums), 10)

    @mock.patch('lastfm.requests.get')
    @mock.patch('lastfm.chart_list')
    def test_get_albums(self, mock_chart, mock_get):
        mock_resp = mock.Mock()
        mock_resp.json.return_value = self.fake_albums_resp
        mock_get.return_value = mock_resp
        albums = lastfm.top_albums('J_Roche', dt.date(2015, 7, 1),
                                   charts=self.charts)
        mock_chart.assert_not_called()
        self.assertEqual(len(albums), 10)

    @mock.patch('lastfm.requests.get')
    def test_get_albums_out_of_range(self, mock_get):
        mock_resp = mock.Mock()
        mock_resp.json.return_value = self.fake_albums_resp
        mock_get.return_value = mock_resp
        with self.assertRaises(lastfm.LastFMException):
            lastfm.top_albums('J_Roche', dt.date(2015, 9, 1),
                              charts=self.charts)


class AppTestCase(unittest.TestCase):

    def setUp(self):
        web_app.app.config['TESTING'] = True
        self.app = web_app.app.test_client()
        data = load_fake_data()
        self.charts = data['charts']

    def test_home(self):
        rv = self.app.get('/')
        assert 'Basic Page' in rv.data

    @mock.patch('lastfm.top_albums')
    @mock.patch('lastfm.chart_list')
    def test_snapshot(self, chart_list_mock, albums_mock):
        chart_list_mock.return_value = self.charts
        web_app.lastfm_snapshot('J_Roche')
        self.assertEqual(albums_mock.call_count, 3)

    @mock.patch('app.lastfm_snapshot')
    def test_valid_user(self, snapshot_mock):
        snapshot_mock.return_value = {
            'six_months': [{'album': 'WILDHEART', 'artist': 'Miguel'}],
            'one_year': [],
            'two_year': [],
        }
        rv = self.app.get('/J_Roche/')
        snapshot_mock.assert_called_with('J_Roche')
        assert 'J_Roche' in rv.data
        assert 'Miguel - WILDHEART' in rv.data

    @mock.patch('app.lastfm_snapshot')
    def test_invalid_user(self, snapshot_mock):
        snapshot_mock.side_effect = lastfm.LastFMException("User not found")
        rv = self.app.get('/J_Roche99/')
        self.assertEqual(rv.status_code, 404)

    @mock.patch('app.lastfm_snapshot')
    def test_api_issue(self, snapshot_mock):
        snapshot_mock.side_effect = lastfm.LastFMException("Some LastFM error")
        rv = self.app.get('/J_Roche99/')
        self.assertEqual(rv.status_code, 200)
        assert 'error' in rv.data


if __name__ == '__main__':
    unittest.main()
