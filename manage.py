#!/usr/bin/env python
#
# ***********************************
# |docname| - Command-line management
# ***********************************
# Execute ``python manage.py`` for a list of available commands.
import os
from runestone import create_app, db
from runestone.model import Course, LogInfo
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    return dict(app=app, db=db, Course=Course, LogInfo=LogInfo)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
