import datetime
from flask import Flask, render_template, jsonify, request, make_response, session, redirect, url_for
import os
from werkzeug.utils import secure_filename
from db_upload import upload_blob
from firestore_manager import get_course_names_for_user
from firestore_manager import get_courses_lec_lng
from firestore_manager import update_course_user
from firestore_manager import get_lecture_by_name
from firestore_manager import get_departments
from firestore_manager import delete_course_from_user

#####################################################################################
# Delete if socket breaks															#
#####################################################################################
from flask_socketio import SocketIO, send, emit


from firestore_manager import *
#log = logging.getLogger('Easy-Lecture')
app = Flask(__name__)
temp_dir = '/tmp'
app.secret_key = "..."
app.config['SESSION_TYPE'] = 'filesystem'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join('keys', 'vthacks7.json')


socketio = SocketIO(app)

@app.route('/')
@app.route('/index', methods=['GET'])
def index():
	if (session.get('logged_in') is None) or not session['logged_in']:
		return redirect(url_for('login'))
	else:
		return render_template('index.html')


@app.route('/test')
def test():
	return render_template('test.html')


@app.route('/get_users_courses', methods=['POST'])
def get_users_courses():
	if (session.get('logged_in') is None) or not session['logged_in']:
		return redirect(url_for('login'))
	if request.method == 'POST':
		# print(session["username"])
		# return jsonify(get_course_names_for_user("nateb@vt.edu"))
		return jsonify(get_course_names_for_user(session["username"]))


@app.route('/get_courses_lectures', methods=['POST'])
def get_courses_lectures():
	if (session.get('logged_in') is None) or not session['logged_in']:
		return redirect(url_for('login'))
	if request.method == 'POST':
		return jsonify(get_courses_lec_lng(request.form["department"], request.form["course_no"]))

@app.route('/login',  methods=['POST', 'GET'])
def login():
	if session.get('logged_in') and  session['logged_in']:
		return redirect(url_for("index"))
	if (request.method == 'POST'):
		session["username"] = request.form["username"]
		session["user_type"] = request.form["user_type"]
		session["logged_in"] = True
		print(session['user_type'])
		print(session['username'])
		return redirect(url_for("index"))
	elif request.method == 'GET':
		return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
	if session.get('logged_in') and  session['logged_in']:
		session.clear()
	return redirect(url_for("login"))

@app.route('/manage_courses')
def manage_courses():
	return render_template('manage_courses.html')


@app.route('/upload')
def upload():
	if (session.get('logged_in') is None) or not session['logged_in']:
		return redirect(url_for('login'))
	return render_template('upload.html')

@app.route('/upload_video', methods=['GET','POST'])
def upload_lecture():
	if (session.get('logged_in') is None) or not session['logged_in']:
		return redirect(url_for('login'))
	video = request.files['file']
	video_name = secure_filename(video.filename)
	print(video_name)

	#audio = request.files['audio']
	#audio_name = secure_filename(audio.filename)
	#print(audio_name)
	#save_path = os.path.join(temp_dir, video_name)
	#with open(save_path, 'w') as f:

	video.save(os.path.join(temp_dir,video_name))

	#audio.save(os.path.join(temp_dir, audio_name))

	#upload_blob(temp_dir, video_name, audio_name)
	upload_blob(temp_dir, video_name)
	return render_template('upload_success.html')

@app.route('/upload_wait')
def upload_wait():
	if (session.get('logged_in') is None) or not session['logged_in']:
		return redirect(url_for('login'))
	return render_template('upload_wait.html')


@app.route('/courses')
def courses():
	if (session.get('logged_in') is None) or not session['logged_in']:
		return redirect(url_for('login'))
	return render_template("courses.html")

@app.route('/update_user', methods=['POST'])
def update_user():
	if (session.get('logged_in') is None) or not session['logged_in']:
		return redirect(url_for('login'))
	if request.method == 'POST':
		dep = request.form['department']
		num = request.form['course_no']

		update_course_user(dep, num, session['username'])
		return redirect(url_for("courses"))

@app.route('/lecture', methods=['GET'])
def lecture():
	if (session.get('logged_in') is None) or not session['logged_in']:
		return redirect(url_for('login'))
	dep = request.args.get('dep')
	cno = request.args.get('cno')
	lec = request.args.get('lec')
	
	print("{}\t{}\t{}".format(dep, cno, lec))
	
	data = get_lecture_by_name(dep, cno, lec)
  
	if (data == None):
		return render_template("error.html")

	d = dict()
	for i in range(len(data['words'])):
		word = data['words'][i].lower()
		time = int((data['timestamps'][i]) / 1000000000)
		if word not in d:
			d[word] = list()
		d[word].append(time)

	l = list()
	for key in d:
		new_d = dict()
		new_d['word'] = key
		new_d['arr'] = d[key]
		l.append(new_d)

	data['word_struct'] = l
	return render_template('lecture.html', cno=cno, lec=lec, dep=dep, data=data)

@app.route('/get_depts', methods=['POST'])
def depts():
	if request.method == 'POST':
		return jsonify(get_departments())


@app.route('/get_dept_courses', methods=['POST'])
def get_dept_courses():
	if request.method == 'POST':
		return jsonify(get_courses_by_department(request.form['dept']))

@app.route('/delete_course', methods=['POST'])
def delete_course():
	dep = request.form['department']
	num = request.form['course_no']
	print(dep + " , " + num + " , " + session['username'] )
	delete_course_from_user(session['username'], dep, num)
	return jsonify({})

#####################################################################################
# Here Begins the scary live chat stuff												#
#####################################################################################

@socketio.on('connect')
def handle_connect():
	#print("connected")
	emit('test', {"data": "this is a message"})

@socketio.on('chat-msg')
def handle_message(json):
	print(str(json))
	json['username'] = session['username'];
	json['user_type'] = session['user_type']
	emit('update', json, broadcast=True)


if __name__ == '__main__':
	app.secret_key = "..."
	app.config['SESSION_TYPE'] = 'filesystem'
	os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join('keys', 'vthacks7.json')
	socketio.run(app, host='127.0.0.1', port=8080, debug=True)
