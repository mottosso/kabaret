'''



'''



from kabaret.core.apps.base import App
from kabaret.core.conf import Config, Group, Attribute, ConfigError

#
#    SETTINGS
#
class User(object):
    _LOGINS = set()

    def __init__(self, login, mail=None):
        super(User, self).__init__()
        if login in self.__class__._LOGINS:
            raise Exception('Duplicate declaration of user %r'%(login,))
        self.__class__._LOGINS.add(login)
        self.login = login
        self.mail = mail
        
class Team(object):
    _NAMES = set()
    
    def __init__(self, name, *users):
        super(Team, self).__init__()
        if name in self.__class__._NAMES:
            raise Exception('Duplicate declaration of team %r'%(name,))
        self.__class__._NAMES.add(name)
        self.name = name
        self.users = users
        
class UsersAppSettings(Config):
    '''
    The Users App Configuration.

    You must build some user and optionally put them in 
    teams, and put them in the USERS and TEAMS config attribute:
        dee = User('dee', mail='dee@my_compagny.com')
        zwib = User('zwib', mail='zwib@your_compagny.com')
        
        dev = Team(dee, zwib)
        setup = Team(zwib)
    
        USERS = [
            dee,
            zwib,
        ]
        TEAMS = [
            dev,
            setup,
        ]
    
    You can use those variable here:
        User:          the class used to declare users.
        Team:          the class used to declare teams.
        project_name:  the name of the project
        store_path:    the store path for the project
        station_class: the name of the staion class (Windows-7, Linux, etc...)
        APP:           the SYSCMD app loading this configuration

    '''
    EXTRA_CONTEXT = {
        'User': User,
        'Team': Team,
    }
    
    def _define(self):
        self.USERS = Attribute(
            [],
            '''
            The list of users. Each item must be an
            instance of 'User'.
            Users found in team and not here will be 
            added here (you need only to declare users not
            belonging to any team).
            '''
        )
            
        self.TEAMS = Attribute(
            [],
            '''
            The list of teams. Each item must be an
            instance of 'Team'.
            '''
        )
            
            
#
#    APP
#
class UsersApp(App):
    APP_KEY = 'USERS'
    REQ_APPS = ['DB']

    def __init__(self, host):
        super(UsersApp, self).__init__(host)
        self._db_user_collection = None
        self._db_team_collection = None
        self._users = []
        self._teams = []
        
    def _get_setting_context(self):
        return {
            'project_name' : self.host.project_name,
            'store_path' : self.host.station_config.store_path,
            'station_class' : self.host.station_config.station_class,
            'APP': self,
        }
        
    def _get_setting_class(self):
        return UsersAppSettings
    
    def _apply_settings(self, settings):
        self.users = settings.USERS
        self.login_to_user = dict([ (user.login, user) for user in self.users ])
        
        self.teams = settings.TEAMS
        print '#------- Teams:'
        for team in self.teams:
            if team.name == 'All':
                raise Exception('The team name "All" is reserved.')
            print '   ', team.name, [ user.login for user in team.users ]
            for user in team.users:
                if user.login not in self.login_to_user:
                    self.users.append(user)
                    self.login_to_user[user.login] = user

        print '#------- Users:'
        for user in self.users:
            print '   ', user.login, user.mail or "<no mail>"
        
        self.teams.append(Team('All', *self.users))
        
    def _host_init_done(self):
        self._db_user_collection = self.DB.get_collection('USERS.users')
        self._db_team_collection = self.DB.get_collection('USERS.teams')
    
    def get_all_logins(self):
        return [ user.login for user in self.users ]
    
    def get_teams(self):
        return dict(
            [ 
                (team.name, [ user.login for user in team.users ])
                for team in self.teams
            ]
        )

    def get_user(self, login):
        return self.login_to_user.get(login)
    
    def get_user_data(self, login, data_id, default):
        data = self._db_user_collection.get(
            {'_id': login},
            'user_data.%s'%(data_id,),
            default
        )
        #print 'GET USER DATA', login, data_id
        #print ' ->', data
        return data

    def set_user_data(self, login, data_id, data):
        self._db_user_collection.set(
            {'_id': login},
            'user_data.%s'%(data_id,),
            data,
        )
        
    def set_user_data_key(self, login, data_id, key, value):
        data = self.get_user_data(login, data_id, {})
        if value is None:
            try:
                del data[key]
            except KeyError:
                return  # was not there, did not remove it = nothing to save
        else:
            data[key] = value
        self.set_user_data(login, data_id, data)

    def append_to_user_data(self, login, data_id, value):
        data = self.get_user_data(login, data_id, [])
        data.append(value)
        self.set_user_data(login, data_id, data)
        
#
#    APP Commands
#
from kabaret.core.apps.command import Command, CommandError, Arg

@UsersApp.cmds.register
class GetUserMail(Command):
    '''
    Returns the mail defined for the given user or None 
    if the user does not have a mail defined in the app settings.
    
    If the user was not found, None is returned.
    '''
    login=Arg()
    def doit(self):
        user = self.app.get_user(self.login)
        return user and user.mail or None

@UsersApp.cmds.register
class GetUserData(Command):
    '''
    Returns the user data (a dict) with the given id for the given login.
    If the data id does not exists, an empty dict is returned.
    
    If key is not None, only this key in the data is returned.
    If no such key exists in the data, the default value is 
    returned.
    
    '''
    login=Arg()
    data_id=Arg()
    key=Arg()
    default=Arg()
    def doit(self):
        data = self.app.get_user_data(self.login, self.data_id, {})
        if self.key is None:
            return data
        return data.get(self.key, self.default)


@UsersApp.cmds.register
class AppendToUserData(Command):
    '''
    Appends to the value of a key in a user data.
    If the key exists in the user data, it must be a list.
    If the key does not exists in the user data, an empty list is stored first.
    '''
    login=Arg()
    data_id=Arg()
    value=Arg()
    def doit(self):
        if None in (self.login, self.data_id, self.key):
            raise CommandError('The command arguments "login" and "data_id" cannot be None.')
        self.app.append_to_user_data(self.login, self.data_id, self.value)

@UsersApp.cmds.register
class SetUserData(Command):
    '''
    Sets the value of a key in a user data.
    If the key is None, the value will be set as the whole user data dict.
    
    If the key is not None but the value is None, the key is removed from the 
    user data.
    '''
    login=Arg()
    data_id=Arg()
    key=Arg()
    value=Arg()
    def doit(self):
        if None in (self.login, self.data_id):
            raise CommandError('The command arguments "login" and "data_id" cannot be None.')
        if self.key is None:
            self.app.set_user_data(self.login, self.data_id, self.value)
        else:
            self.app.set_user_data_key(self.login, self.data_id, self.key, self.value)
            
            