class ParsedData:
    def __init__(self, input_data):
        self.command = None
        self.name = None
        self.password = None
        self.arg1 = None
        self.arg2 = None

        split = input_data.split()
        if len(split) > 0:
            self.command = split[0]
        if len(split) > 1:
            self.name = split[1]
        if len(split) > 2:
            self.password = split[2]
        if len(split) > 3:
            self.arg1 = split[3]
        if len(split) > 4:
            self.arg2 = ' '.join(split[4:])

    def __str__(self):
        return f'command: {self.command}, name: {self.name}, password: {self.password}, arg1: {self.arg1}, arg2: {self.arg2}'
