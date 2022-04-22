from utils.Logger import Logger
import os,sys

class Authentication:
    def __init__(self):
        #logger = Logger().get_logger()
        sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
        #print(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

        print(sys.path)
        from utils.Logger import Logger



obj = Authentication()
