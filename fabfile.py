from fabric.api import env, prompt, put, hide, run, local, prefix, sudo, settings, output, roles
from contextlib import contextmanager
from fabric.context_managers import cd, shell_env
from fabric.decorators import task, parallel

import config

output['aborts'] = False

env.user = config.USER
env.password = config.PASSWORD
env.command_timeout = 30
env.roledefs = {
				"local" : config.LOCAL_HOSTS,
				"staging" : config.STAGING_HOSTS
			}
errors = {}

PATH_TO_APP = "/home/ubuntu/workspace/testpress/testpress_python/testpress"
PATH_TO_VIR_ENV = "export WORKON_HOME=/home/ubuntu/workspace/; . /usr/local/bin/virtualenvwrapper.sh; workon testpress"

def rollback():
	print ("********* Failed to execute deploy! ===> " + env.host_string)
	print (errors)

@contextmanager
def failwrapper():
	""" Called if any command fails.
	"""
	try:
	    yield
	except SystemExit as e:
	    errors[env.host_string] = str(e.message)
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
@roles("local")
def execute_manage_local():
	""" Execute 'manage' file of django testpress.
	"""
	with manage_fabric_execution():
		with project():
			run ("./manage.py migrate_schemas --settings=testpress.settings.remote")

@task
@parallel
@roles("staging")
def execute_manage_staging(app, current_migration):
	""" Execute 'manage' file of django testpress on staging(Arguments:app, current_migration).

	parameter:
	app: In which app migration is updated.
	current_migration: what is the new migration number.
	"""
	current_migration = int(current_migration)
	with manage_fabric_execution():
		with project():
			run ("./manage.py migrate_schemas --fake apps." + app + " 00" + str(current_migration - 2) + " --settings=testpress.settings.local")
			run ("./manage.py migrate_schemas --fake apps." + app + " 00" + str(current_migration - 1) + " --settings=testpress.settings.local")
			run ("./manage.py migrate_schemas --fake apps." + app + " 00" + str(current_migration) + " --settings=testpress.settings.local")
			run ("./manage.py migrate_schemas apps." + app + " 00" + str(current_migration) + " --settings=testpress.settings.local")

@task
@parallel
def restart_gunicorn():
	""" Restart gunicorn and celeryd on host.
	"""
	with manage_fabric_execution():
		with virtualenv():
			sudo ("supervisorctl restart gunicorn")

@task
@parallel
def restart_celeryd():
	""" Restart gunicorn and celeryd on host.
	"""
	with manage_fabric_execution():
		with virtualenv():
			sudo ("supervisorctl restart gunicorn")

@task
@parallel
def deploy():
	""" Update code and restart server.
	"""
	update()
	requirements()
	execute_manage()
	restart_gunicorn()
	restart_celeryd()
	print ("********* Successfully deploy! ===> " + env.host_string)

@task
@parallel
@roles("staging")
def deploy_staging(app, current_migration):
	""" Update code and restart staging server(Arguments:app, current_migration).

	parameter:
	app: In which app migration is updated.
	current_migration: what is the new migration number.
	"""
	update()
	requirements()
	execute_manage_staging(app=app,current_migration=current_migration)
	restart_gunicorn()
	print ("********* Successfully deploy! ===> " + env.host_string)
