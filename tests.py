import datetime as dt
import json
import mock
import unittest

from app import app
import lastfm


class LastFMTestCase(unittest.TestCase):

    def setUp(self):
        with open('fixtures/chart.json', 'r') as f:
            self.fake_chart_resp = json.loads(f.read())
        with open('fixtures/albums.json', 'r') as f:
            self.fake_albums_resp = json.loads(f.read())
        self.charts = []
        for chart in self.fake_chart_resp['weeklychartlist']['chart']:
            self.charts.append({
                'from': chart['from'],
                'to': chart['to'],
                'from_date': lastfm.timestamp_to_date(chart['from']),
                'to_date': lastfm.timestamp_to_date(chart['to']),
            })

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
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_home(self):
        rv = self.app.get('/')
        assert 'Basic Page' in rv.data


if __name__ == '__main__':
    unittest.main()
