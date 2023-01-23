import datetime


class Message:
    def __init__(self, sender, recipient, content, read_by_recipient=False, time_sent=datetime.datetime.now()):
        self.sender_name = sender.name
        self.recipient_name = recipient.name
        self.content = content
        self.read_by_recipient = read_by_recipient
        self.time_sent = time_sent
