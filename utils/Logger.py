import json
import logging
import logging.config
import datetime

class Logger:
    def __init__(self):
        with open('logger.json','rt') as file:
            config = json.load(file)

        logging.config.dictConfig(config)


        self.logger = logging.getLogger()


        file_name = str(datetime.datetime.today()).split(' ')[0]
        file_name += '.log'

        file_handler = logging.FileHandler(filename=file_name)
        file_handler.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)


    def get_logger(self):
        return self.logger


