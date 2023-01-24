import datetime


class Message:
    def __init__(self, sender_name, recipient_name, content, read_by_recipient=False,
                 time_sent=None):
        self.sender_name = sender_name
        self.recipient_name = recipient_name
        self.content = content
        self.read_by_recipient = read_by_recipient

        if time_sent:
            self.time_sent = time_sent
        else:
            self.time_sent = datetime.datetime.now()
