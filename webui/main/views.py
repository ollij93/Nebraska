from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

import json
import os
import sys
sys.path.insert(0, '../../nebraska')

from nebraska import common

# Create your views here.
def index(requests):
	config = json.load(open(common.NEBRASKA_DIR + '/config.json'))
	parameters = config['ids']

	cache = json.load(open(common.NEBRASKA_DIR + '/cache.json'))

	chart_js_dates = 'var dates = ['
	chart_js_balances = 'var balnc = ['

	for tran in cache["accounts"][0]["transactions"]:
		chart_js_dates += 'Date(' + str(tran["date"]) + '), '
		chart_js_balances += str(tran["balance_after"]) + ", "

	chart_js_dates += '];'
	chart_js_balances += '];'

	with open(os.path.dirname(__file__) + '/static/main/chart_script.js', 'r+') as chart_js:
		chart_js_text = chart_js.read()

		chart_js_text = chart_js_text.replace('var dates = [];', chart_js_dates)
		chart_js_text = chart_js_text.replace('var balnc = [];', chart_js_balances)

		print(chart_js_text)

		chart_js.seek(0)
		chart_js.write(chart_js_text)

	return render(requests, 'main/index.html', parameters)