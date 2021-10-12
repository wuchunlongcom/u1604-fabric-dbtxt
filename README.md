
###优质代码：u1604-fabric-dbtxt
```
一、使用说明：
进入py366
$ source /Users/wuchunlong/local/py366/env/bin/activate
进入目录：$ cd /Users/wuchunlong/local/github/abbytraining/Controller/complete/u1604/u1604-fabric-dbtxt

（一）配置fabricrc
hosts = 47.100.52.110
user = root
password = qazx@1234

uuid = 5b3794134d48
project_name = ProjectName
gunicorn_port = 8000
python_ver = 3
domain = www.wuchunlong.cn

git_name = wuchunlong0
git_user = Django-Rest-Framework
git_email = wcl6005%40163.com
git_password = ******

git_db_passwd = ******

（二）环境
1、部署环境Python 3.6.6；
2、工程应用名必须为：mysite

（三）命令行执行命令，开始一键部署：
(env) ...$ python -V
Python 3.6.6
(env)$ fab -c fabricrc init_deploy_u1604


二、对“文相部署源代码u1604”修改记录：
1、2019.01.12 修改一次。
2、2019.01.13 修改一次。
3、2019.01.15 将数据库数据压缩备份文件db.txt，上传到与代码同一个git。
删除了configure_db_repo()、修改了fabricrc、deployconfig/backupdb.py
4、2019.04.14 问题： 新建仓库不能实现每一分钟更新一次db.txt
修改了fabricrc、deployconfig/backupdb.py
修改了fabfile.py中的 def configure_crontab():

三、主要功能：
1、一键部署。
2、数据库自动备份。对数据库数据压缩备份，自动上传到git保存（与代码同一个git）。

四、自动更新配置：deployconfig/backupdb.crontab
*/1 * * * * python {remote_website_dir}/tool/backupdb.py
数据库数据变化后，每一分钟更新一次db.txt

五、测试 数据库自动备份
1、登录网页，通过admin后台，删除一些记录，记住时间
2、在远程仓库 例如：https://github.com/wcl6005/wuchunlong 查看db.txt，显示相对应的删除记录时间 20190414[07:47:14]，说明定时任务工作正常（数据库自动备份工作正常）。
```

#-------------------------------------------------------------------#
## Reference
- [fabric reference](http://docs.fabfile.org/en/2.3/getting-started.html)

## Pre-Requirement
- Django
- DB
	- if set git_db_url, copy git_db_url/demo.sqlite3 src/mysite/production.sqlite3 
	- else, cp src/mysite/demo.sqlite3 src/mysite/production.sqlite3

## QuickStart

1. `git clone https://github.com/wu-wenxiang/Project-Python-Webdev`
1. `cd Project-Python-Webdev/u1604-fabric`
1. `virtualenv -p python3 env`
1. `. env/bin/activate`
1. `pip install -r requirements.txt`
1. `cp .fabricrc fabricrc`，然后修改fabricrc文件
1. `fab -c fabricrc init_deploy_u1604`
1. [Demo]()
1. 用户名 / 密码：admin / 56e1E@ab1234
