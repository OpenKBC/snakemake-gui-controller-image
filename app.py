__author__ = "Junhee Yoon"
__version__ = "1.0.2"
__maintainer__ = "Junhee Yoon"
__email__ = "swiri021@gmail.com"

# Flask related libraries
from flask import Flask, request, render_template, redirect, url_for, session
from flask_bootstrap import Bootstrap
from models import InitForm

# Flask apps libraries
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from flask_wtf.csrf import CSRFProtect

# Additional function libraries
import yaml
import uuid
import os
import subprocess
import glob

# Custom form making
from wtforms.validators import InputRequired
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

# Celery running
import json
from celery import Celery, current_task
from celery.result import AsyncResult
from subprocess import Popen, PIPE

# Internal libraries
from libraries.handlers import yamlHandlers


app = Flask(__name__)

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY # CSRF key
app.config['WTF_CSRF_TIME_LIMIT']=None

## Celery setting
app.config.update(
    CELERY_BROKER_URL='redis://redis:6379/0', # Redis docker
    CELERY_RESULT_BACKEND='redis://redis:6379/0'
)
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    return celery
celery = make_celery(app)

# set Bootstrap
Bootstrap(app)

# setting Navigation Bar
nav = Nav(app)

@nav.navigation()
def mynavbar():
    return Navbar( 'Workflow Controller', View('Home', 'home') )
nav.init_app(app)

# setting CSRF protector
csrf = CSRFProtect()
csrf.init_app(app)


#########Route###########
# Actual function
@app.route("/", methods=['GET', 'POST'])
def home():
    """
    Landing page and selecting pipeline to control
    """
    #session.clear() # When it gets back, clear session data
    session['_id'] = uuid.uuid4().hex # random session id for recognize diffent snakemake running
    form = InitForm(request.form)

    # Getting 'data' from pipeline selector and redirect to yaml creator
    if form.validate_on_submit():
        session['selected_pipeline'] = form.pipeline_name.data # create session data for passing value
        return redirect(url_for('config_yaml_creator'))

    return render_template( 'home.html', title="Snakemake controller", form=form)


@app.route("/yamlcreator", methods=['GET', 'POST'])
def config_yaml_creator():
    """
    Making a form by parsing config.yaml
    """

    # Frame Form, could be added default setting for snakemake commandline
    class SnakeMakeForm(FlaskForm):
        pass;

    val = session.get('selected_pipeline', None) # yaml path
    yaml_data = yamlHandlers._parsing_yamlFile(val) # Parsing yaml data

    for key, value in yaml_data.items(): # Loop with yaml keys
        setattr(SnakeMakeForm, key, StringField(key, validators=[InputRequired()], render_kw={'placeholder': value})) # set key with yaml key and placehoder with value
    setattr(SnakeMakeForm, 'submit', SubmitField('Submit')) # Make submit button on the bottomss
    form = SnakeMakeForm(request.form) # set form

    if form.validate_on_submit():
        result_yaml_data={} # result dictionary
        # order is same as form order
        for formData, yamlKeys in zip(form, yaml_data.keys()):
            result_yaml_data[yamlKeys]=formData.data
        
        yaml_output = yamlHandlers._reform_yamlFile(val, result_yaml_data, str(session.get('_id', None))) # make result yaml file
        session['yaml_output'] = yaml_output
        return redirect(url_for('workflow_status'))

    return render_template('config_yaml_creator.html', form=form)

@celery.task()
def workflow_running(pipeline_path, yaml_file):
    proc = Popen(['conda', 'run', '-n', 'pipeline_controller_base', 'snakemake', '--snakefile', pipeline_path+'Snakefile',\
        '--cores', str(3), '--directory', pipeline_path, '--configfile', yaml_file], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    print(" ".join(['conda', 'run', '-n', 'pipeline_controller_base', 'snakemake', '--snakefile', pipeline_path+'Snakefile',\
        '--cores', str(3), '--directory', pipeline_path, '--configfile', yaml_file]))
    # It is not working with snakemake
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        current_task.update_state(state='PROGRESS', meta={'msg': str(line)})
    return 999

@app.route("/workflow_progress")
def workflow_progress():
    jobid = request.values.get('jobid')
    print(jobid)
    if jobid:
        job = AsyncResult(jobid, app=celery)
    print(job.state)
    if job.state == 'PROGRESS':
        return json.dumps(dict( state=job.state, msg=job.result['msg'],))

    elif job.state == 'SUCCESS':
        return json.dumps(dict( state=job.state, msg="done",))

    elif job.state == 'FAILURE':
        return json.dumps(dict( state=job.state, msg="failture",)) ## return somewhere to exit
    return '{}'

@app.route("/status")
def workflow_status():
    pipeline_path = session.get('selected_pipeline', None) # Pipeline path
    yaml_file = session.get('yaml_output', None) # yaml file

    job = workflow_running.delay(pipeline_path, yaml_file)
    return render_template('progress.html', JOBID=job.id)

#########Route###########

if __name__ == '__main__':
    app.run(host='0.0.0.0')