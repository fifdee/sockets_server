class User:
    def __init__(self, name, password, permission='USER'):
        self.name = name
        self.password = password
        self.permission = permission

    def __eq__(self, other):
        return self.name == other.name and self.password == other.password

    def get_conversations(self):
        ...

    def get_unread_message(self):
        ...

    @staticmethod
    def get_usernames():
        from database_manager import DatabaseManager
        return [user.name for user in DatabaseManager.get_users()]

    def send_message(self):
        ...
