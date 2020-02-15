import datetime
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
	if request.method == 'POST':
		return jsonify({})
	elif request.method == 'GET':
		return render_template('login.html')

@app.route('/add_course')
def add_course():
    return render_template('add_course.html')
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
