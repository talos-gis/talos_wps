import os
import flask

from pywps import Service

from processes import processes

app = flask.Flask(__name__)


# This is, how you start PyWPS instance
service = Service(processes, ['pywps.cfg'])


@app.route('/wps', methods=['GET', 'POST'])
def wps():
    return service


@app.route('/')
def hello():
    return 'hello to the WPS server root'


@app.route('/test')
def test():
    return 'hello test!'


def flask_response(targetfile):
    if os.path.isfile(targetfile):
        file_ext = os.path.splitext(targetfile)[1]
        with open(targetfile, mode='rb') as f:
            file_bytes = f.read()
        mime_type = None
        if 'xml' in file_ext:
            mime_type = 'text/xml'
        return flask.Response(file_bytes, content_type=mime_type)
    else:
        flask.abort(404)


@app.route('/outputs/' + '<path:filename>')
def outputfile(filename):
    targetfile = os.path.join('', 'outputs', filename)
    flask_response(targetfile)


@app.route('/data/' + '<path:filename>')
def datafile(filename):
    targetfile = os.path.join('', 'data', filename)
    flask_response(targetfile)
