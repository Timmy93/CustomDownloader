#!/usr/bin/env python3
from flask import Flask

app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def hello_world():
	return "<p>Hello, World!</p>"


@app.route("/ciao", methods=['GET', 'POST'])
def hello2_world():
	return "<p>Ciao!</p>"


if __name__ == "__main__":
	app.run(port=5081, host='0.0.0.0', debug=True, use_reloader=False)
