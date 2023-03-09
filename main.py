from flask import Flask, request, send_file
import os
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
import tempfile
import shutil

app = Flask(__name__)
Gst.init(None)

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return 'No file part in the request', 400

    file = request.files['file']

    if file.filename == '':
        return 'No selected file', 400

    tmp_file = tempfile.NamedTemporaryFile(delete = False)
    tmp_file.write(file.read())
    tmp_file.close()

    pipeline_str = f'filesrc location={tmp_file.name} ! decodebin ! x264enc ! mp4mux ! filesink location={tmp_file.name}.mp4'

    pipeline = Gst.parse_launch(pipeline_str)
    pipeline.set_state(Gst.State.PLAYING)

    bus = pipeline.get_bus()

    msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE,
         Gst.MessageType.ERROR | Gst.MessageType.EOS)

    pipeline.set_state(Gst.State.NULL)

    if msg.type == Gst.MessageType.ERROR:
        os.remove(tmp_file.name)
        return f'Error converting file: {msg.parse_error()}'

    return send_file(tmp_file.name + ".mp4", mimetype='video/mp4', as_attachment=True, download_name=tmp_file.name)

    os.remove(tmp_file.name)

if __name__ == "__main__":
    app.run(debug=True)
