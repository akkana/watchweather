#!/usr/bin/env python3

from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def hello_world():
    return '''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>Test Page</title>
</head>

<body>

<h1>Test Page</h1>

<p>
Hello, world!

</body>
</html>'''

@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id

@app.route('/report1/<stationname>')
def report1(stationname):
    return "Report from %s" % stationname

@app.route('/report/<stationname>', methods=['POST', 'GET'])
def report(stationname):
    if request.method == 'POST':
        print("Got a report:", request, request.form)
        print("Keys:", ', '.join(list(request.form.keys())))
        retstr = ''
        for key in request.form:
            retstr += '%s: %s\n' % (key, request.form[key])
        print("Returning:'''%s'''" % retstr)
        return retstr

    #     if valid_login(request.form['username'],
    #                    request.form['password']):
    #         return log_the_user_in(request.form['username'])
    #     else:
    #         error = 'Invalid username/password'

    # the code below is executed if the request method
    # was GET or the credentials were invalid
    # return render_template('login.html', error=error)
    return "Error: request.method was %s" % request.method

