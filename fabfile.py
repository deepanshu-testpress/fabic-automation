from fabric.api import env, prompt, put, hide, run, local, prefix, sudo, settings, output
from contextlib import contextmanager
from fabric.context_managers import cd, shell_env
from fabric.decorators import task, parallel

import config

output['aborts'] = False

env.hosts = config.HOSTS
env.user = config.USER
env.password = config.PASSWORD
env.command_timeout = 30

PATH_TO_APP = "/home/ubuntu/workspace/testpress/testpress_python/testpress"
PATH_TO_VIR_ENV = "export WORKON_HOME=/home/ubuntu/workspace/; . /usr/local/bin/virtualenvwrapper.sh; workon testpress"

def rollback():
	print ("********* Failed to execute deploy! ===> " + env.host_string)

@contextmanager
def failwrapper():
	""" Called if any command fails.
	"""
	try:
	    yield
	except SystemExit as e:
	    rollback()
	    raise

@contextmanager
def virtualenv():
	""" Runs commands within the project's virtualenv.
	"""
	with prefix(PATH_TO_VIR_ENV):
		yield

@contextmanager
def environmental_variable():
	""" Set environmental variables for testpress django.
	"""
	with shell_env(EMAIL_HOST=config.EMAIL_HOST,
				   EMAIL_PORT=config.EMAIL_PORT,
				   EMAIL_HOST_USER=config.EMAIL_HOST_USER,
				   EMAIL_HOST_PASSWORD=config.EMAIL_HOST_PASSWORD,
				   DEFAULT_FROM_EMAIL=config.DEFAULT_FROM_EMAIL,
				   SERVER_EMAIL=config.SERVER_EMAIL,
				   SECRET_KEY=config.SECRET_KEY,
				   DATABASE_NAME=config.DATABASE_NAME,
				   DATABASE_USER=config.DATABASE_USER,
				   DATABASE_USER_PASSWORD=config.DATABASE_USER_PASSWORD,
				   AWS_STORAGE_BUCKET_NAME=config.AWS_STORAGE_BUCKET_NAME,
				   AWS_ACCESS_KEY_ID=config.AWS_ACCESS_KEY_ID,
				   AWS_SECRET_ACCESS_KEY=config.AWS_SECRET_ACCESS_KEY,
				   GOOGLE_API_KEY=config.GOOGLE_API_KEY):
		yield

@contextmanager
def project():
    """ Runs commands within the project's directory.
    """
    with virtualenv():
    	with environmental_variable():
    		with cd(PATH_TO_APP):
    			yield

@contextmanager
def manage_output():
	""" Hide the warnings, errors, commands and outputs of host on local.
	"""
	with settings(hide('output', 'warnings', 'stderr')):
		yield

@contextmanager
def manage_fabric_execution():
	""" Manage output and errors of hosts on local
	"""
	with failwrapper():
		with manage_output():
			yield

@task
@parallel
def update():
	""" Fetch latest code from git.
	"""
	with manage_fabric_execution():
		with cd(PATH_TO_APP):
			run ("git pull")

@task
@parallel
def requirements():
	""" Execute requirement files with pip.
	"""
	with manage_fabric_execution():
		with project():
			output = run('ls requirements/')
			files = output.split()
			for file in files:
				run ("pip install -r requirements/" + file)

@task
@parallel
def execute_manage():
	""" Execute 'manage' file of django testpress.
	"""
	with manage_fabric_execution():
		with project():
			run ("./manage.py migrate_schemas --settings=testpress.settings.remote")

@task
@parallel
def restart():
	""" Restart gunicorn and celeryd on host.
	"""
	with manage_fabric_execution():
		with virtualenv():
			sudo ("supervisorctl restart gunicorn")
			sudo ("supervisorctl restart celeryd")


@task
@parallel
def deploy():
	""" Update code and restart server.
	"""
	update()
	requirements()
	execute_manage()
	restart()
	print ("********* Successfully deploy! ===> " + env.host_string)
