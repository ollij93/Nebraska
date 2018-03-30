from django.shortcuts import render

import json
import sys
sys.path.insert(0, '../../nebraska')

from nebraska import common

# Create your views here.
def index(requests):
	config = json.load(open(common.NEBRASKA_DIR + '/config.json'))
	parameters = config['ids']
	return render(requests, 'main/index.html', parameters)