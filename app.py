import datetime as dt
from flask import Flask, render_template, abort, request, redirect, url_for
import lastfm
import logging


app = Flask(__name__)


# Set up logging
handler = logging.StreamHandler()
log_fmt = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
handler.setFormatter(log_fmt)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST' and request.form['username']:
        url = url_for('user_page', username=request.form['username'])
        print url
        return redirect(url)
    return render_template('home.html')


@app.route('/<username>/')
def user_page(username):
    error_message = None
    try:
        charts = lastfm_snapshot(username)
    except lastfm.LastFMException as e:
        charts = None
        error_message = str(e)
        app.logger.error("%s - %s" % (username, error_message))
        if 'User not found' in error_message:
            return abort(404)
    app.logger.info("Loaded data for %s" % username)
    return render_template('user.html', username=username, charts=charts,
                           error=error_message)


def lastfm_snapshot(username):
    charts = lastfm.chart_list(username)
    six_months_ago = dt.date.today() - dt.timedelta(days=6*30)
    six_months = lastfm.top_albums(username, six_months_ago, charts=charts)
    one_year_ago = dt.date.today() - dt.timedelta(days=365)
    one_year = lastfm.top_albums(username, one_year_ago, charts=charts)
    two_year_ago = dt.date.today() - dt.timedelta(days=2*365)
    two_year = lastfm.top_albums(username, two_year_ago, charts=charts)
    three_year_ago = dt.date.today() - dt.timedelta(days=3*365)
    three_year = lastfm.top_albums(username, three_year_ago, charts=charts)
    four_year_ago = dt.date.today() - dt.timedelta(days=4*365)
    four_year = lastfm.top_albums(username, four_year_ago, charts=charts)
    five_year_ago = dt.date.today() - dt.timedelta(days=5*365)
    five_year = lastfm.top_albums(username, five_year_ago, charts=charts)
    charts = {
        'six_months': six_months,
        'one_year': one_year,
        'two_year': two_year,
        'three_year': three_year,
        'four_year': four_year,
        'five_year': five_year,
    }
    return charts


if __name__ == '__main__':
    app.run(debug=True)
    app.logger.setLevel(logging.DEBUG)
