import unittest
from unittest.mock import Mock

from database_manager_postgres import DatabaseManager
from response import Response
from user import User


class ResponseWithTestDatabaseTest(unittest.TestCase):
    def setUp(self):
        db_params = ("172.30.56.61", "test_server_db", "dev", "dev")
        db_params_sqlite = (None, "server_db.db", None, None)

        self.server = Mock()
        self.server.version = '0.0.1'
        self.server.uptime = 30.5
        self.db_mngr = DatabaseManager(*db_params_sqlite)
        self.db_mngr.add_user(User('username123', '123123'))
        self.db_mngr.add_user(User('admin123', '456456', permission='ADMIN'))
        self.db_mngr.add_user(User('user_with_full_mailbox', 'asdasd'))
        for i in range(5):
            Response(f'whisper username123 123123 user_with_full_mailbox message number {i}', self.server)

    def tearDown(self):
        self.db_mngr.clear_users_table()
        self.db_mngr.clear_messages_table()
        self.db_mngr.stop_db_connections()

    def test_response_for_wrong_command(self):
        response = Response('  skakl \n oo', self.server)
        self.assertEqual('Unknown command', response.data)

    def test_response_as_json(self):
        response = Response('xxxxx', self.server)
        self.assertEqual('"Unknown command"', response.as_json.data)

    def test_response_as_bytes(self):
        response = Response('xxxxx', self.server)
        self.assertEqual(b'Unknown command', response.as_bytes.data)

    def test_response_for_info_command(self):
        response = Response('info', self.server)
        self.assertEqual('Server version: 0.0.1', response.data)

    def test_response_for_uptime_command(self):
        response = Response('uptime', self.server)
        self.assertEqual('Server uptime: 30.5 s', response.data)

    def test_response_for_help_command(self):
        response = Response('help', self.server)
        self.assertTrue('Available commands' in response.data)

    def test_response_for_stop_command(self):
        response = Response('stop', self.server)
        self.assertEqual(None, response.data)

    def test_response_for_signup_command_no_credentials(self):
        response = Response('signup', self.server)
        self.assertEqual('Make sure to provide username and password.', response.data)

    def test_response_for_signup_command_new_credentials(self):
        response = Response('signup new_user new_password_123', self.server)
        self.assertEqual(f'User created: new_user', response.data)

    def test_response_for_signup_command_taken_credentials(self):
        response = Response('signup username123 123123', self.server)
        self.assertEqual('This username is already taken.', response.data)

    def test_response_for_login_command_no_credentials(self):
        response = Response('login', self.server)
        self.assertEqual('Make sure to provide username and password.', response.data)

    def test_response_for_login_command_wrong_credentials(self):
        response = Response('login not_existing zxczxc', self.server)
        self.assertEqual('Incorrect credentials.', response.data)

    def test_response_for_login_command_correct_credentials(self):
        response = Response('login username123 123123', self.server)
        self.assertEqual('Logged in as username123', response.data)

    def test_response_for_login_command_correct_credentials_as_admin(self):
        response = Response('login admin123 456456', self.server)
        self.assertEqual('Logged in as admin123 (admin)', response.data)

    def test_response_for_users_command_no_login_credentials(self):
        response = Response('users', self.server)
        self.assertEqual('Log in first.', response.data)

    def test_response_for_users_command_wrong_login_credentials(self):
        response = Response('users wrong_username pw123123', self.server)
        self.assertEqual('Incorrect credentials.', response.data)

    def test_response_for_users_command_correct_login_credentials(self):
        response = Response('users username123 123123', self.server)
        self.assertEqual('admin123, user_with_full_mailbox, username123', response.data)

    def test_response_for_whisper_command_no_login_credentials(self):
        response = Response('whisper', self.server)
        self.assertEqual('Log in first.', response.data)

    def test_response_for_whisper_command_wrong_login_credentials(self):
        response = Response('whisper wrong_username pw123123', self.server)
        self.assertEqual('Incorrect credentials.', response.data)

    def test_response_for_whisper_command_correct_login_credentials_no_recipient(self):
        response = Response('whisper username123 123123', self.server)
        self.assertEqual('Username or message not provided.', response.data)

    def test_response_for_whisper_command_correct_login_credentials_wrong_recipient(self):
        response = Response('whisper username123 123123 wrong_recipient message', self.server)
        self.assertEqual('User "wrong_recipient" does not exist on the server.', response.data)

    def test_response_for_whisper_command_correct_login_credentials_recipient_is_sender(self):
        response = Response('whisper username123 123123 username123 message', self.server)
        self.assertEqual('You cannot whisper yourself.', response.data)

    def test_response_for_whisper_command_correct_login_credentials_correct_recipient_no_message(self):
        response = Response('whisper username123 123123 admin123', self.server)
        self.assertEqual('Username or message not provided.', response.data)

    def test_response_for_whisper_command_correct_login_credentials_correct_recipient_correct_message(self):
        response = Response('whisper username123 123123 admin123 Hello, my friend! How are you?', self.server)
        self.assertEqual('Message "Hello, my friend! How are you?" sent to "admin123"', response.data)

    def test_response_for_whisper_command_correct_login_credentials_recipient_mailbox_full(self):
        response = Response('whisper username123 123123 user_with_full_mailbox Hello, my friend!', self.server)
        self.assertEqual('Mailbox of user "user_with_full_mailbox" is full. You cannot send another message.',
                         response.data)

    def test_response_for_whisper_command_correct_login_credentials_correct_recipient_message_too_long(self):
        too_long_message = ''.join(['x' for x in range(256)])
        response = Response(f'whisper username123 123123 admin123 {too_long_message}', self.server)
        self.assertEqual('Too long message. Maximum character count is 255.', response.data)

    def test_response_for_unread_command_no_login_credentials(self):
        response = Response(f'unread', self.server)
        self.assertEqual('Log in first.', response.data)

    def test_response_for_unread_command_wrong_login_credentials(self):
        response = Response(f'unread username123 zxczxc', self.server)
        self.assertEqual('Incorrect credentials.', response.data)

    def test_response_for_unread_command_correct_login_credentials_empty_mailbox(self):
        response = Response(f'unread username123 123123', self.server)
        self.assertEqual('There are no new messages.', response.data)

    def test_response_for_unread_command_correct_login_credentials_1_message(self):
        Response(f'whisper admin123 456456 username123 message 1', self.server)

        response = Response(f'unread username123 123123', self.server)
        self.assertTrue(f'\nFrom: "admin123", Message: "message 1", Time sent: ' in response.data)

    def test_response_for_conversation_command_no_login_credentials(self):
        response = Response(f'conversation', self.server)
        self.assertEqual('Log in first.', response.data)

    def test_response_for_conversation_command_wrong_login_credentials(self):
        response = Response(f'conversation username123 zxczxc', self.server)
        self.assertEqual('Incorrect credentials.', response.data)

    def test_response_for_conversation_command_correct_login_credentials_no_conversations(self):
        response = Response(f'conversation admin123 456456', self.server)
        self.assertEqual('You have no conversations with other users.', response.data)

    def test_response_for_conversation_command_correct_login_credentials_with_conversations(self):
        response = Response(f'conversation username123 123123', self.server)
        self.assertEqual('You have conversations with these users: user_with_full_mailbox', response.data)

    def test_response_for_conversation_command_correct_login_credentials_not_existing_username(self):
        response = Response(f'conversation username123 123123 not_existing_username', self.server)
        self.assertEqual('You have no messages with not_existing_username.', response.data)

    def test_response_for_conversation_command_correct_login_credentials_existing_username(self):
        response = Response(f'conversation username123 123123 user_with_full_mailbox', self.server)
        correct_response = 'Messages with "user_with_full_mailbox" (oldest to newest):' \
                           '\nusername123: message number 0\nusername123: message number 1' \
                           '\nusername123: message number 2\nusername123: message number 3' \
                           '\nusername123: message number 4'
        self.assertEqual(correct_response, response.data)

    def test_response_for_conversation_command_correct_login_credentials_two_users_not_admin(self):
        response = Response(f'conversation username123 123123 admin123 user_with_full_mailbox', self.server)
        self.assertEqual('Only ADMIN can access other users conversations.', response.data)

    def test_response_for_conversation_command_correct_login_credentials_two_users_admin_no_messages(self):
        response = Response(f'conversation admin123 456456 username123 not_existing_username', self.server)
        self.assertEqual('There are no messages between "username123" and "not_existing_username".', response.data)

    def test_response_for_conversation_command_correct_login_credentials_two_users_admin_with_messages(self):
        response = Response(f'conversation admin123 456456 username123 user_with_full_mailbox', self.server)
        correct_response = 'Messages between "username123" and "user_with_full_mailbox" (oldest to newest):' \
                           '\nusername123: message number 0\nusername123: message number 1' \
                           '\nusername123: message number 2\nusername123: message number 3' \
                           '\nusername123: message number 4'
        self.assertEqual(correct_response, response.data)
