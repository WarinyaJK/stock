from fs_parser import fs_parser
from configparser import ConfigParser
from utils.Logger import Logger
import sys

logger = Logger().get_logger()

class main_class:
    def __init__(self):
        logger.debug('start financial statemnt doc parser program')
        self.load_config()

        #obj = fs_parser()


    def load_config(self):
        logger.debug('load_config')
        parser = ConfigParser()
        config_file = 'config_file.txt'
        
        if len(sys.argv) > 1:
            config_file = sys.argv[1]
        parser.read(config_file)

        corp_list_file = parser.get('corp', 'corp_list_file')
        f = open(corp_list_file)
        self.corp_list = f.readlines()

        start_year = parser.getint('opt', 'start_year')
        end_year = parser.getint('opt', 'end_year')

        self.bs_years = []
        for data in range(start_year, end_year+1):
            self.bs_years.append(str(data))
           # print(data)



        #logger.debug(self.corp_list)

    def start_parser(self):
        for data in self.corp_list:
            obj = fs_parser(data, self.bs_years)
            obj.parse_fs()
            obj.parse_stock_cnt()
            obj.parse_stock_price()
            obj.cal_mc()
            obj.make_csv()
            #obj.display_data()





if __name__ == '__main__':
    obj = main_class()
    obj.start_parser()
