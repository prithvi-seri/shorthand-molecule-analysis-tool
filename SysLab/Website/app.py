import os
from flask import Flask, render_template, request, redirect, url_for
from backend import analyse

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jpe', 'jp2', 'webp'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './Python/SysLab/Website/static'

@app.route('/')
def default():
    return redirect(url_for('upload'))

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/edit', methods = ['POST'])
def edit():
    # handle the file
    file = request.files['file']
    extension = file.filename.rsplit('.', 1)[1].lower()
    filepath = app.config['UPLOAD_FOLDER'] + '/inputImage.' + extension
    print(filepath)
    if  '.' in file.filename and extension in ALLOWED_EXTENSIONS: # check that file is in one of the allowed formats
        if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])       # static folder is invisible for some reason
        file.save(filepath)  # file will always be named 'inputImage'

    return render_template('edit.html', ext = extension)

@app.route('/draw')
def draw():
    return render_template('draw.html')

@app.route('/analysis', methods = ['POST'])
def process():
    # handle the file
    file = request.files['file']
    extension = file.filename.rsplit('.', 1)[1].lower()
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'inputImage.' + extension)
    if  '.' in file.filename and extension in ALLOWED_EXTENSIONS: # check that file is in one of the allowed formats
        if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])       # static folder is invisible for some reason
        file.save(filepath)  # file will always be named 'inputImage'

    # analyze the image and render the template
    formula, vertices = analyse(filepath)
    return render_template('analysis.html', formula = formula, vertices = vertices, ext = extension)

app.debug = True        # change to False
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)