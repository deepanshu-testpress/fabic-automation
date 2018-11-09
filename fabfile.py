from fabric.api import env, prompt, put, run, local, prefix, sudo, settings
from contextlib import contextmanager
from fabric.context_managers import cd, shell_env
from fabric.decorators import task

import config

#env.hosts = config.HOSTS
env.hosts = ["206.189.140.116"]

# env.user = config.USER
# env.password = config.PASSWORD
env.user = "root"
env.password = "ds@12527"

class FabricException(Exception):
    pass

# It will put a file in remote server to check if virtual box is activate or not.
# def check_env():
#     put("check_venv.py", "/home/ubuntu/workspace/check_venv.py")
#     run("python /home/ubuntu/workspace/check_venv.py")

def update_code():
	with settings(abort_exception=FabricException):
	    try:
	        run ("git pull")
	        return True
	    except FabricException:
	        return False

def install_requirements():
	output = run('ls requirements/')
	files = output.split()
	for file in files:
		run ("pip install -r requirements/" + file)

@task
def run_server():
	with prefix("export WORKON_HOME=/home/ubuntu/workspace/; . /usr/local/bin/virtualenvwrapper.sh; workon testpress"):	
		# To check if environment is activated or not.
		# check_env()

		with cd("/home/ubuntu/workspace/testpress/testpress_python/testpress"):
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
				# install all the requirements
				install_requirements()

				# Check if code is updated with git.
				if update_code():
					run ("./manage.py migrate_schemas --settings=testpress.settings.remote")
					# run ("sudo supervisorctl restart gunicorn")
					# run ("sudo supervisorctl restart celeryd")
