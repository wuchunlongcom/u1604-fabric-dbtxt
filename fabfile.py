# -*- encoding: utf-8 -*-

import os
import datetime
from fabric.api import (cd, env, lcd, put, prompt, local, sudo, run,
                        prefix, shell_env, settings, hide)
from fabric.utils import warn

git_url = 'https://{}:{}@github.com/{}/{}'.format(env.git_email, \
    env.git_password, env.git_name, env.git_user)

project_name = '{}-{}'.format(env.project_name, env.uuid)
local_app_dir = './'
local_config_dir = './deployconfig'

remote_app_dir = '/home/www'
remote_git_dir = '/home/git'
remote_website_dir = '{}/{}'.format(remote_app_dir, project_name)
remote_nginx_enable_dir = '/etc/nginx/sites-enabled'
remote_nginx_avail_dir = '/etc/nginx/sites-available'
remote_supervisor_dir = '/etc/supervisor/conf.d'

nowDate = datetime.datetime.now()
NOW_MARK = '%04d%02d%02d%02d%02d%02d' % (nowDate.year, nowDate.month,
                                         nowDate.day, nowDate.hour, 
                                         nowDate.minute, nowDate.second)

def init_os(config_os):
    sudo('if [ -f /etc/apt/sources.list ];then cp /etc/apt/sources.list '
         '/etc/apt/sources.list.$(date +"%y%m%d%H%M%S");fi')

    config_os()

    sudo('pip install virtualenv')
    sudo('apt-get install -y ssh vim')
    sudo('apt-get install -y nginx')
    sudo('apt-get install -y supervisor')
    sudo('apt-get install -y git')
    sudo('apt-get install -y gettext')
    sudo('apt-get install -y libffi-dev libssl-dev libxml2-dev libxslt1-dev '
         'libjpeg8-dev zlib1g-dev')

    sudo('rm -rf {}'.format(remote_website_dir))
    sudo('mkdir -p "{}"'.format(remote_app_dir))
    sudo('chmod -R 777 {}'.format(remote_app_dir))
    sudo('mkdir -p "{}"'.format(remote_website_dir))
    sudo('chown -R {}:{} {}'.format(env.user, env.user, remote_website_dir))
    with cd(remote_website_dir):
        run('virtualenv -p python{} env'.format(env.python_ver))
        run('mkdir -p logs tool')
        run('crontab -l | grep -v "python {}" | crontab'.format(remote_website_dir))

def config_u1604():
    with lcd(local_config_dir):
        with cd('/etc/apt'):
            put('./sources-u1604.list', './', use_sudo=True)
    sudo('apt-get update')
    sudo('apt-get install -y python-minimal python-dev python-pip')
    sudo('apt-get install -y python3 python3-dev python3-pip')    

def copy_project_dir():
    with cd(remote_website_dir):
        run(r'[ ! -d src  ] && git clone {} src '
            '|| [ false ]'.format(git_url))
        run(r'cd src && git pull && cd -')
        with prefix(r'source env/bin/activate'):
            run(r'pip install -r src/requirements.txt')
            run(r'cd src/mysite && rm -rf static '
                '&& python manage.py collectstatic '
                '&& cd -')
        run(r'cp src/mysite/db.sqlite3 src/mysite/production.sqlite3') #add 2019.01.12

def recover_sqlite_db():
    with cd(remote_website_dir):
        run('if [ -f ./production.sqlite3.%s ]; '
            'then cp ./production.sqlite3.%s mysite/production.sqlite3; '
            'fi' % (NOW_MARK, NOW_MARK))

def configure_db_repo():  #  fab -c fabricrc  configure_db_repo
    with cd(remote_website_dir):
        run(r'[ ! -d db ] && git clone {} db '
            '|| [ false ]'.format(env.git_db_url))
        run(r'[ -d db ] && cd db && git pull && cd - || [ false ]')
        run(r'[ ! -d db ] '
            '&& cp src/mysite/demo.sqlite3 src/mysite/production.sqlite3 '
            '|| [ false ]')
        run(r'[ -d db ] '
            '&& cp db/demo.sqlite3 src/mysite/production.sqlite3 '
            '|| [ false ]')
        
#在远程主机仓库，创建一个初始的数据库压缩文件(含密码) add 2019.01.13 db.txt  fab -c fabricrc  init_db_txt
def init_db_txt(): 
    with cd(remote_website_dir):
        with cd('src'):
            run('rm -rf db.txt && '
                'mkdir -p db1 && '  
                'chmod -R 777 db1 && '
                'cp ./mysite/db.sqlite3 ./db1/production.sqlite3 && '
                'tar -zcvf - db1|openssl des3 -salt -k "%s" | dd of=db.txt && '
                'rm -rf db1 && '
                'git add . && git commit -a -m "add" && git push || [ false ]' %(env.git_db_passwd))  

def configure_crontab():
    with lcd(local_config_dir):
        confStr = open('{}/backupdb.crontab'.format(local_config_dir)).read()
        confStr = confStr.replace("{remote_website_dir}", remote_website_dir)
        open('{}/.backupdb.crontab.tmp'.format(local_config_dir), "w").write(confStr)
        with cd(remote_website_dir):
            put('./.backupdb.crontab.tmp', 'tool/', use_sudo=True)
            
        confStr = open('{}/backupdb.py'.format(local_config_dir)).read()
        confStr = confStr.replace("{remote_website_dir}", remote_website_dir)
        confStr = confStr.replace("{db_zip_password}", env.git_db_passwd)
        confStr = confStr.replace("{email}", env.git_email) #add
        confStr = confStr.replace("{name}", env.git_name) #add
        open('{}/.backupdb.py.tmp'.format(local_config_dir), "w").write(confStr)
        with cd(remote_website_dir):
            put('./.backupdb.py.tmp', 'tool/backupdb.py', use_sudo=True)
            
    run('(crontab -l; cat {}/tool/.backupdb.crontab.tmp) '
        '| sort | uniq | crontab'.format(remote_website_dir))

def configure_nginx():
    sudo('/etc/init.d/nginx stop')
    sudo('rm -rf {}/{}'.format(remote_nginx_enable_dir, 'default'))
    sudo('rm -rf {}/{}'.format(remote_nginx_enable_dir, project_name))
    sudo('rm -rf {}/{}'.format(remote_nginx_avail_dir, project_name))
    with lcd(local_config_dir):
        confStr = open('{}/nginx.conf'.format(local_config_dir)).read()
        confStr = confStr.replace("{remote_website_dir}", remote_website_dir)
        confStr = confStr.replace("{gunicorn_port}", env.gunicorn_port)
        confStr = confStr.replace("{domain}", env.domain)
        open('{}/.nginx.conf.tmp'.format(local_config_dir), "w").write(confStr)
        with cd(remote_nginx_avail_dir):
            put('./.nginx.conf.tmp', './{}'.format(project_name), use_sudo=True)
    sudo('ln -s {}/{} {}/{}'.format(
        remote_nginx_avail_dir, project_name,
        remote_nginx_enable_dir, project_name
    ))
    sudo('/etc/init.d/nginx start')

def configure_supervisor():
    sudo('supervisorctl stop {}'.format(project_name))
    sudo('rm -rf {}/{}.conf'.format(remote_supervisor_dir, project_name))
    with lcd(local_config_dir):
        confStr = open('{}/supervisor.conf'.format(local_config_dir)).read()
        confStr = confStr.replace("{remote_website_dir}", remote_website_dir)
        confStr = confStr.replace("{project_name}", project_name)
        confStr = confStr.replace("{user}", env.user)
        confStr = confStr.replace("{gunicorn_port}", env.gunicorn_port)
        open('{}/.supervisor.conf.tmp'.format(local_config_dir), "w").write(confStr)
        with cd(remote_supervisor_dir):
            put('./.supervisor.conf.tmp', './{}.conf'.format(project_name), use_sudo=True)
    sudo('supervisorctl reread')
    sudo('supervisorctl update')

def configure_git():
    """
    1. Setup bare Git repo
    2. Create post-receive hook
    3. Change owner of git repo
    """
    sudo('mkdir -p "{}"'.format(remote_git_dir))
    with cd(remote_git_dir):
        sudo('mkdir {}.git'.format(project_name))
        with cd('{}.git'.format(project_name)):
            sudo('git init --bare')
            with lcd(local_config_dir):
                with cd('hooks'):
                    put('./post-receive', './', use_sudo=True)
                    sudo('chmod +x post-receive')
        sudo('chown -R {}:{} ./'.format(env.user, env.user))

def run_app():
    with cd(remote_website_dir):
        sudo('supervisorctl start {}'.format(project_name))

def restart_app():
    with cd(remote_website_dir):
        sudo('supervisorctl restart {}'.format(project_name))

def install_mysql():
    sudo('apt-get install -y debconf-utils')
    with settings(hide('warnings', 'stderr'), warn_only=True):
        result = sudo('dpkg-query --show mysql-server')
    if result.failed is False:
        warn('MySQL is already installed')
        return
    mysql_password = prompt('Please enter MySQL root:')
    sudo('echo "mysql-server-5.5 mysql-server/root_password password ' \
        '{}" | debconf-set-selections'.format(mysql_password))
    sudo('echo "mysql-server-5.5 mysql-server/root_password_again password ' \
        '{}" | debconf-set-selections'.format(mysql_password))

    with shell_env(DEBIAN_FRONTEND='noninteractive'):
        sudo('apt-get -y --no-upgrade install {}'.format(
            ' '.join(['mysql-server', 'mysql-client']))
        )
        sudo('mysql_secure_installation')
    sudo('apt-get install -y python-mysqldb')

def db_migrate():
    """ sync up database after update the production"""
    app_config_file = '{}/config/production.py'.format(remote_website_dir)
    with cd(remote_website_dir):
        with shell_env(APP_CONFIG_FILE=app_config_file):
            with prefix('source env/bin/activate'):
                run('python manage.py syncdb')
                run('python manage.py init')

def status():
    sudo('supervisorctl status')

def push_deploy():
    """
    1. Commit new files
    2. Restart gunicorn via supervisor
    """
    with lcd(local_app_dir):
        local('git add -A')
        commit_message = prompt("Commit message?")
        local('git commit -am "{}"'.format(commit_message))
        local('git push production master')
    db_migrate()
    restart_app()

def _deploy():
    init_db_txt()
    configure_crontab()
    configure_nginx()
    configure_supervisor()
    restart_app()

def deploy():
    copy_project_dir()
    _deploy()

def deployRecover():
    copy_project_dir()
    recover_sqlite_db()
    _deploy()

# fab -c fabricrc init_deploy_u1604
def init_deploy_u1604():
    init_os(config_u1604)
#    install_mysql()
    deploy()

