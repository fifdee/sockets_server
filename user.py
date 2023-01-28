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
        if self in DatabaseManager.get_users():
            self.permission = User.get_user_by_name(self.name).permission
            return True
        else:
            return False

    @property
    def in_database(self):
        from database_manager import DatabaseManager
        return self.name in [user.name for user in DatabaseManager.get_users()]

    @property
    def unread_messages(self):
        from database_manager import DatabaseManager
        return [msg for msg in DatabaseManager.get_messages() if
                msg.recipient_name == self.name and not msg.read_by_recipient]

    def get_conversations(self):
        from database_manager import DatabaseManager

        msgs = [msg for msg in DatabaseManager.get_messages() if
                msg.recipient_name == self.name or msg.sender_name == self.name]
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

        msgs = [msg for msg in DatabaseManager.get_messages() if
                (msg.recipient_name == self.name and msg.sender_name == other_name) or
                (msg.recipient_name == other_name and msg.sender_name == self.name)]

        return msgs

    def get_unread_count(self):
        from database_manager import DatabaseManager
        unread_messages = [msg for msg in DatabaseManager.get_messages() if
                           msg.recipient_name == self.name and not msg.read_by_recipient]
        return len(unread_messages)

    @staticmethod
    def get_all_usernames():
        from database_manager import DatabaseManager
        return sorted([user.name for user in DatabaseManager.get_users()])

    @staticmethod
    def get_user_by_name(name):
        from database_manager import DatabaseManager
        return [user for user in DatabaseManager.get_users() if user.name == name][0]

    @staticmethod
    def get_messages(username1, username2):
        from database_manager import DatabaseManager

        msgs = [msg for msg in DatabaseManager.get_messages() if
                (msg.recipient_name == username1 and msg.sender_name == username2) or
                (msg.recipient_name == username2 and msg.sender_name == username1)]

        return msgs
