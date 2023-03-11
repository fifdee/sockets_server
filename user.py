class User:
    def __init__(self, name, password, permission="USER"):
        self.name = name
        self.password = password
        self.permission = permission

    def __eq__(self, other):
        return self.name == other.name and self.password == other.password

    def __str__(self):
        return f'User name: {self.name}, password: {self.password}, permission: {self.permission}'

    @property
    def credentials_ok(self):
        from database_manager import DatabaseManager
        user_from_db = DatabaseManager.instance.get_user(self.name)

        if user_from_db:
            if self == user_from_db:
                self.permission = user_from_db.permission
                return True
        return False

    @property
    def in_database(self):
        from database_manager import DatabaseManager
        user_from_db = DatabaseManager.instance.get_user(self.name)

        if user_from_db:
            return True
        else:
            return False

    @property
    def unread_messages(self):
        from database_manager import DatabaseManager
        unread_messages_from_db = DatabaseManager.instance.get_unread_messages(self.name)
        return unread_messages_from_db

    def get_conversations(self):
        from database_manager import DatabaseManager

        msgs = DatabaseManager.instance.get_messages(self.name)
        sender_names = [msg.sender_name for msg in msgs]
        recipient_names = [msg.recipient_name for msg in msgs]
        unique_names = set(sender_names + recipient_names)
        try:
            unique_names.remove(self.name)
        except KeyError:
            ...

        return unique_names

    def get_messages_with_other(self, other_name):
        from database_manager import DatabaseManager
        msgs = DatabaseManager.instance.get_messages(self.name, other_name)

        return msgs

    def get_unread_count(self):
        from database_manager import DatabaseManager
        unread_messages_from_db = DatabaseManager.instance.get_unread_messages(self.name)
        return len(unread_messages_from_db)

    @staticmethod
    def get_all_usernames():
        from database_manager import DatabaseManager

        return sorted(DatabaseManager.instance.get_usernames())

    @staticmethod
    def get_user_by_name(name):
        from database_manager import DatabaseManager

        return DatabaseManager.instance.get_user(name)

    @staticmethod
    def get_messages(username1, username2):
        from database_manager import DatabaseManager
        msgs = DatabaseManager.instance.get_messages(username1, username2)

        return msgs
