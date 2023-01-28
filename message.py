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

    def __eq__(self, other):
        return self.sender_name == other.sender_name and \
            self.recipient_name == other.recipient_name and \
            self.content == other.content and \
            self.read_by_recipient == other.read_by_recipient and \
            self.time_sent == other.time_sent

    def __str__(self):
        return f"""sender_name: {self.sender_name}
        recipient_name: {self.recipient_name}
        content: {self.content}
        read_by_recipient: {self.read_by_recipient}
        time_sent: {self.time_sent}"""
