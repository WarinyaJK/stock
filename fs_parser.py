from utils.Logger import Logger
import xml.etree.ElementTree as ET
import requests


logger = Logger().get_logger()

class fs_parser:
    def __init__(self, corp_info, bs_years):
        logger.debug('start parsing financial statemnt doc')
        self.corp_name = corp_info.split("\t")[0]
        stock_code = corp_info.split("\t")[1].split("\n")[0]
        logger.debug("%s,%s",self.corp_name, stock_code)
        self.corp_code = self.parse_xml(stock_code)
        self.api_key = '3a281b27a21c3dc22614bbf2d8fe3a6266550fe3'
        self.bs_years = bs_years




    def parse_xml(self, stock_code):
        root = ET.parse('CORPCODE.xml').getroot()
        tag = root.findall('list')

        corp_code = ''

        for data in tag:
            if data[2].text == stock_code:
                print(data[1].text)
                print(data[0].text)
                corp_code = data[0].text
                break

        return corp_code

    def parse_fs(self):
        reprt_code = ['11011','11013','11012','11014']

        y_revenu_dict = {}
        y_income_dict= {}
        y_cf_dict = {}
        for year in self.bs_years:
            t_year = year
            fs_div = 'CFS'
            y_revenu = []
            y_income = []
            y_cf =[]
            for code in reprt_code:
                t_code = code
                response = requests.get("https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json", params={"crtfc_key": self.api_key, 
                                                                                         "corp_code": self.corp_code,
                                                                                        "bsns_year": t_year,
                                                                                         "reprt_code" : t_code,
                                                                                         "fs_div" : fs_div
                                                                                        })
                logger.debug('%s%s', t_year,t_code)
                if response.json()['status'] == '013':
                    logger.debug("no have data")
                    continue
                aa = response.json()['list']
        
                #print(response.json()['list'])

                revenu_flag = 0
                for data in aa:
                    if 'ifrs_Revenue' == data['account_id'] and revenu_flag==0:
                        logger.debug('%s %s','매출', data['thstrm_amount'])
                        y_revenu.append(int(data['thstrm_amount']))
                        revenu_flag = 1
                    elif 'ifrs-full_Revenue' == data['account_id'] and revenu_flag==0:
                        logger.debug('%s %s','매출', data['thstrm_amount'])
                        y_revenu.append(int(data['thstrm_amount']))
                        revenu_flag = 1
                    elif 'ifrs-full_GrossProfit' == data['account_id'] and revenu_flag==0:
                        logger.debug('%s %s','매출', data['thstrm_amount'])
                        y_revenu.append(int(data['thstrm_amount']))
                        revenu_flag = 1
                    elif 'ifrs_GrossProfit' == data['account_id'] and revenu_flag==0:
                        logger.debug('%s %s','매출', data['thstrm_amount'])
                        y_revenu.append(int(data['thstrm_amount']))
                        revenu_flag = 1
                
                    if 'dart_OperatingIncomeLoss' == data['account_id']:
                        logger.debug('%s %s', '영업이익', data['thstrm_amount'])
                        y_income.append(int(data['thstrm_amount']))
        
                    if 'ifrs_CashFlowsFromUsedInOperatingActivities' == data['account_id'] or 'ifrs-full_CashFlowsFromUsedInOperatingActivities' == data['account_id']:
                        logger.debug('%s %s','현금흐름',data['thstrm_amount'])
                        y_cf.append(int(data['thstrm_amount']))
                
                #dict_ = {'매출액' : [data['thstrm_amount'],data['frmtrm_amount'],data['bfefrmtrm_amount']]}
    
            y_revenu_dict[t_year] = y_revenu
            y_income_dict[t_year] = y_income
            y_cf_dict[t_year] = y_cf


#obj = fs_parser()
        

        

"""
from utils.Logger import Logger
#from dart_fss import get_corp_list
#import dart_fss as dart
import requests
import xml.etree.ElementTree as ET

logger = Logger().get_logger()

class fs_parser:
    def __init__(self, bsns_year='2020', reprt_code='11011', fs_div='CFS'):
        logger.debug('start financial statemnt doc parser program')
        self.api_key = '3a281b27a21c3dc22614bbf2d8fe3a6266550fe3'
        dart.set_api_key(api_key=self.api_key)

        self.corp_code = self.get_corp_code()
        print(self.corp_code)
        self.bsns_year = bsns_year
        self.reprt_code = reprt_code
        self.fs_div = fs_div


    def get_corp_code(self, code='003850'):
        #xml_file = 
        
        corp_list = get_corp_list()
        return (corp_list.find_by_stock_code(code).to_dict()['corp_code'])
        

    def get_corp_data(self):
        self.response = requests.get("https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json", 
                params={"crtfc_key": self.api_key,
                        "corp_code": self.corp_code,
                        "bsns_year": self.bsns_year,
                        "reprt_code" : self.reprt_code,
                        "fs_div" : self.fs_div
                        })
        #logger.debug(response.json()['list'])

    def parse_data(self):
        aa = self.response.json()['list']
        for data in aa:
            if '매출액' in data['account_nm']:
                logger.debug(data['thstrm_amount'])
                logger.debug(data['frmtrm_amount'])
                logger.debug(data['bfefrmtrm_amount'])
            if '영업이익' in data['account_nm']:
                logger.debug(data['thstrm_amount'])
                logger.debug(data['frmtrm_amount'])
                logger.debug(data['bfefrmtrm_amount'])
            if '영업활동' in data['account_nm']:
                logger.debug(data['thstrm_amount'])
                logger.debug(data['frmtrm_amount'])
                logger.debug(data['bfefrmtrm_amount'])












obj = fs_parser(bsns_year='2021')
obj.get_corp_data()
obj.parse_data()
"""

