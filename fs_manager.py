
from utils.Logger import Logger
import xml.etree.ElementTree as ET
import datetime
from pandas import DataFrame
import requests
import FinanceDataReader as fdr
from datetime import date, timedelta
import numpy as np
import math
import openpyxl
import os.path
import pandas as pd



logger = Logger().get_logger()

class fs_manager:
    def __init__(self, corp_info, bs_years):
        logger.info('start parsing financial statemnt doc')
        self.corp_name = corp_info.split("\t")[0]
        self.stock_code = corp_info.split("\t")[1].split("\n")[0]
        self.corp_code = self.parse_xml(self.stock_code)
        self.api_key = '3a281b27a21c3dc22614bbf2d8fe3a6266550fe3'
        self.bs_years = bs_years
        self.total_data = {}
        self.file_name = str(datetime.datetime.today()).split(' ')[0] + '.xlsx'

        logger.info("{}, {}, {}".format(self.corp_name, self.stock_code, self.corp_code))
        logger.info("target years : {} ~ {}".format(self.bs_years[-1], self.bs_years[0]))
    
    def parse_xml(self, stock_code):
        root = ET.parse('CORPCODE.xml').getroot()
        tag = root.findall('list')

        corp_code = ''

        for data in tag:
            if data[2].text == stock_code:
                logger.debug(data[1].text)
                logger.debug(data[0].text)
                corp_code = data[0].text
                break

        return corp_code

    def display_data(self):
        label = ['매출', '1Q', '2Q', '3Q','영업이익','1Q','2Q','3Q','현금흐름','1Q','2Q','3Q','주식수','주가','시가총액','매출성장률','이익성잘률','현금성장률','주가증가율','시총증가율','최소증가율','예측시총','예측주가','괴리율','누적괴리율']
        summary = DataFrame(self.total_data, index=label)
        logger.info(summary)

        #y_revenu_dict = dict(sorted(y_revenu_dict.items()))

    def make_csv(self):
        file_exists = os.path.exists(self.file_name)
        if file_exists == False:
            wb = openpyxl.Workbook()
            wb.save(self.file_name)
        else:
            wb=openpyxl.load_workbook(self.file_name)
            if self.corp_name in wb.get_sheet_names():
                wb.remove_sheet(wb.get_sheet_by_name(self.corp_name))
                wb.save(self.file_name)
        
        label = ['매출', '1Q', '2Q', '3Q','영업이익','1Q','2Q','3Q','현금흐름','1Q','2Q','3Q','주식수','주가','시가총액','매출성장률','이익성잘률','현금성장률','주가증가율','시총증가율','최소증가율','예측시총','예측주가','괴리율','누적괴리율']
        summary = DataFrame(self.total_data, index=label)

        writer = pd.ExcelWriter(self.file_name, engine='openpyxl', mode='a', if_sheet_exists="overlay", float_format='%d')
        summary.to_excel(writer, sheet_name=self.corp_name)
        writer.close()


    def parse_fs(self):
        reprt_code = ['11011','11013','11012','11014']

        y_revenu_dict = {}
        y_income_dict= {}
        y_cf_dict = {}
        
        revenu_tmp_dict = {}
        income_tmp_dict = {}
        cf_tmp_dict = {}
        
        base_year = self.bs_years[0]

        for year in self.bs_years:

            logger.debug(year)

            y_revenu = []
            y_income = []
            y_cf = []

            for code in reprt_code:
                if code == '11011' and (year == base_year-1 or year == base_year-2):
                    logger.debug(revenu_tmp_dict)
                    if revenu_tmp_dict[year] != '':
                        y_revenu.append(int(revenu_tmp_dict[year]))
                        y_income.append(int(income_tmp_dict[year]))
                        y_cf.append(int(cf_tmp_dict[year]))


                    if base_year-2 == year:
                        base_year = year-1
                    
                    if revenu_tmp_dict[year] != '':
                        continue

                response = requests.get("https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json", 
                        params={"crtfc_key": self.api_key, 
                                "corp_code": self.corp_code,
                                "bsns_year": year,
                                "reprt_code" : code,
                                "fs_div" : 'CFS'})

                if response.json()['status'] == '013':
                    logger.debug('CFS do not exist')
                    response = requests.get("https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json", 
                        params={"crtfc_key": self.api_key, 
                                "corp_code": self.corp_code,
                                "bsns_year": year,
                                "reprt_code" : code,
                                "fs_div" : 'OFS'})

                if response.json()['status'] == '013':
                    logger.debug('OFS do not exist')

                    y_revenu.append(0)
                    y_income.append(0)
                    y_cf.append(0)

                    if code == '11011':
                        base_year = year-1
                    continue

                result = response.json()['list']


                revenu_flag = 0
                income_flag = 0
                cf_flag = 0

                #if year == 2017:
                #    logger.debug(result)


                for data in result:
                    if 'ifrs_Revenue' == data['account_id'] and revenu_flag == 0:
                        logger.debug('{} 매출 : {}'.format(code, data['thstrm_amount']))
                        y_revenu.append(int(data['thstrm_amount']))
                        if code == '11011':
                            revenu_tmp_dict[year-1] = int(data['frmtrm_amount'])
                            logger.debug(data['bfefrmtrm_amount'])
                            if data['bfefrmtrm_amount'] == '':
                                revenu_tmp_dict[year-2] = ''
                            else:
                                revenu_tmp_dict[year-2] = int(data['bfefrmtrm_amount'])

                        revenu_flag = 1

                    elif 'ifrs-full_Revenue' == data['account_id'] and revenu_flag == 0:
                        logger.debug('{} 매출 : {}'.format(code, data['thstrm_amount']))
                        y_revenu.append(int(data['thstrm_amount']))
                        if code == '11011':
                            revenu_tmp_dict[year-1] = data['frmtrm_amount']
                            revenu_tmp_dict[year-2] = data['bfefrmtrm_amount']

                        revenu_flag = 1

                    elif 'ifrs-full_GrossProfit' == data['account_id'] and revenu_flag == 0:
                        logger.debug('{} 매출 : {}'.format(code,data['thstrm_amount']))
                        y_revenu.append(int(data['thstrm_amount']))
                        if code == '11011':
                            revenu_tmp_dict[year-1] = data['frmtrm_amount']
                            revenu_tmp_dict[year-2] = data['bfefrmtrm_amount']

                        revenu_flag = 1

                    elif 'ifrs_GrossProfit' == data['account_id'] and revenu_flag == 0:
                        logger.debug('{} 매출 : {}'.format(code, data['thstrm_amount']))
                        y_revenu.append(int(data['thstrm_amount']))
                        if code == '11011':
                            revenu_tmp_dict[year-1] = data['frmtrm_amount']
                            revenu_tmp_dict[year-2] = data['bfefrmtrm_amount']

                        revenu_flag = 1
                                          
                    elif '영업수익' == data['account_nm'] and revenu_flag == 0:
                        logger.debug('{} 매출 : {}'.format(code, data['thstrm_amount']))
                        y_revenu.append(int(data['thstrm_amount']))
                        if code == '11011':
                            revenu_tmp_dict[year-1] = data['frmtrm_amount']
                            revenu_tmp_dict[year-2] = data['bfefrmtrm_amount']

                        revenu_flag = 1
                    
                    elif '매출액' == data['account_nm'] and revenu_flag == 0:
                        logger.debug('{} 매출 : {}'.format(code, data['thstrm_amount']))
                        y_revenu.append(int(data['thstrm_amount']))
                        if code == '11011':
                            revenu_tmp_dict[year-1] = data['frmtrm_amount']
                            revenu_tmp_dict[year-2] = data['bfefrmtrm_amount']

                        revenu_flag = 1


                    
                    if 'dart_OperatingIncomeLoss' == data['account_id'] and income_flag == 0:
                        logger.debug('{} 영업이익 : {}'.format(code ,data['thstrm_amount']))
                        y_income.append(int(data['thstrm_amount']))
                        if code == '11011':
                            income_tmp_dict[year-1] = data['frmtrm_amount']
                            income_tmp_dict[year-2] = data['bfefrmtrm_amount']

                        income_flag = 1

                    elif '영업이익' == data['account_nm'] and income_flag == 0:
                        logger.debug('{} 영업이익 : {}'.format(code ,data['thstrm_amount']))
                        y_income.append(int(data['thstrm_amount']))
                        if code == '11011':
                            income_tmp_dict[year-1] = data['frmtrm_amount']
                            income_tmp_dict[year-2] = data['bfefrmtrm_amount']

                        income_flag = 1

                    
                    if 'ifrs_CashFlowsFromUsedInOperatingActivities' == data['account_id'] and cf_flag == 0: 
                        logger.debug('{} 현금흐름 : {}'.format(code, data['thstrm_amount']))
                        y_cf.append(int(data['thstrm_amount']))
                        if code == '11011':
                            cf_tmp_dict[year-1] = data['frmtrm_amount']
                            cf_tmp_dict[year-2] = data['bfefrmtrm_amount']
                        
                        cf_flag = 1

                    elif 'ifrs-full_CashFlowsFromUsedInOperatingActivities' == data['account_id'] and cf_flag==0:
                        logger.debug('{} 현금흐름 : {}'.format(code, data['thstrm_amount']))
                        y_cf.append(int(data['thstrm_amount']))
                        if code == '11011':
                            cf_tmp_dict[year-1] = data['frmtrm_amount']
                            cf_tmp_dict[year-2] = data['bfefrmtrm_amount']

                        cf_flag = 1

                    elif 'dart_AdjustmentsForAssetsLiabilitiesOfOperatingActivities' == data['account_id'] and cf_flag==0:
                        logger.debug('{} 현금흐름 : {}'.format(code, data['thstrm_amount']))
                        y_cf.append(int(data['thstrm_amount']))
                        if code == '11011':
                            cf_tmp_dict[year-1] = data['frmtrm_amount']
                            cf_tmp_dict[year-2] = data['bfefrmtrm_amount']

                        cf_flag = 1

                    elif 'dart_NetCashflowsFromUsedInOperations' == data['account_id'] and cf_flag==0:
                        logger.debug('{} 현금흐름 : {}'.format(code, data['thstrm_amount']))
                        y_cf.append(int(data['thstrm_amount']))
                        if code == '11011':
                            cf_tmp_dict[year-1] = data['frmtrm_amount']
                            cf_tmp_dict[year-2] = data['bfefrmtrm_amount']

                        cf_flag = 1
                    
                    elif '영업활동으로 인한 순현금흐름' == data['account_nm'] and cf_flag==0:
                        logger.debug('{} 현금흐름 : {}'.format(code, data['thstrm_amount']))
                        y_cf.append(int(data['thstrm_amount']))
                        if code == '11011':
                            cf_tmp_dict[year-1] = data['frmtrm_amount']
                            cf_tmp_dict[year-2] = data['bfefrmtrm_amount']
                        cf_flag = 1
                    
                    elif '영업에서 창출된 현금' == data['account_nm'] and cf_flag==0:
                        logger.debug('{} 현금흐름 : {}'.format(code, data['thstrm_amount']))
                        y_cf.append(int(data['thstrm_amount']))
                        if code == '11011':
                            cf_tmp_dict[year-1] = data['frmtrm_amount']
                            cf_tmp_dict[year-2] = data['bfefrmtrm_amount']
                        cf_flag = 1
                    
                    elif 'dart_ProfitLossForStatementOfCashFlows' == data['account_id'] and cf_flag==0:
                        logger.debug('{} 현금흐름 : {}'.format(code, data['thstrm_amount']))
                        y_cf.append(int(data['thstrm_amount']))
                        if code == '11011':
                            cf_tmp_dict[year-1] = data['frmtrm_amount']
                            cf_tmp_dict[year-2] = data['bfefrmtrm_amount']
                        cf_flag = 1
                    
                    elif '영업활동으로 인한 현금흐름' == data['account_nm'] and cf_flag==0:
                        logger.debug('{} 현금흐름 : {}'.format(code, data['thstrm_amount']))
                        y_cf.append(int(data['thstrm_amount']))
                        if code == '11011':
                            cf_tmp_dict[year-1] = data['frmtrm_amount']
                            cf_tmp_dict[year-2] = data['bfefrmtrm_amount']
                        cf_flag = 1

                    elif 'Ⅰ. 영업활동현금흐름' == data['account_nm'] and cf_flag==0:
                        logger.debug('{} 현금흐름 : {}'.format(code, data['thstrm_amount']))
                        y_cf.append(int(data['thstrm_amount']))
                        if code == '11011':
                            cf_tmp_dict[year-1] = data['frmtrm_amount']
                            cf_tmp_dict[year-2] = data['bfefrmtrm_amount']
                        cf_flag = 1

                        


            y_revenu_dict[year] = y_revenu
            y_income_dict[year] = y_income
            y_cf_dict[year] = y_cf


        y_revenu_dict = dict(sorted(y_revenu_dict.items()))
        self.total_data = y_revenu_dict
        
        for year in self.bs_years:
            for data in y_income_dict[year]:
                self.total_data[year].append(data)
        
        for year in self.bs_years:
            for data in y_cf_dict[year]:
                self.total_data[year].append(data)


    def parse_stock_cnt(self):
        stock_count = []
        reprt_code = ['11011','11013','11012','11014']
        code = '11011'
        p_stock_cnt = 0
        for year in self.bs_years:
            if self.bs_years[0] == year:
                print('this year')
                print(datetime.datetime.today().strftime('%m/%d'))
                mon = int(datetime.datetime.today().strftime('%m'))
                if 4 < mon < 8:
                    code = '11013'
                elif 7 < mon < 11:
                    code = '11012'
                elif 10 < mom:
                    code = '11014'
            
            response = requests.get("https://opendart.fss.or.kr/api/stockTotqySttus.json", 
                    params={"crtfc_key": self.api_key,
                            "corp_code": self.corp_code,
                            "bsns_year": year,
                            "reprt_code" : code
                            })
            if response.json()['status'] == '013':
                stock_count.append(0)
                continue
            
            
            for data in response.json()['list']:
                if '보통주' == data['se']:
                    stock = data['distb_stock_co'].replace(',','')
                    if stock == '-':
                        stock = p_stock_cnt
                    stock_count.append(int(stock))
                    p_stock_cnt = int(stock)
                    break

                elif '의결권 있는 주식' in data['se']:
                    stock = data['distb_stock_co'].replace(',','')
                    if stock == '-':
                        stock = p_stock_cnt
                    stock_count.append(int(stock))
                    p_stock_cnt = int(stock)
                    break
                elif '보 통 주' in data['se']:
                    stock = data['distb_stock_co'].replace(',','')
                    if stock == '-':
                        stock = p_stock_cnt
                    stock_count.append(int(stock))
                    p_stock_cnt = int(stock)
                    break
                elif '합계' in data['se']:
                    stock = data['distb_stock_co'].replace(',','')
                    if stock == '-':
                        stock = p_stock_cnt
                    stock_count.append(int(stock))
                    p_stock_cnt = int(stock)
                    break
        #print(stock_count)

        index = 0
        for year in self.bs_years:
            self.total_data[year].append(stock_count[index])
            index = index+1

    def parse_stock_price(self):
        stock_price = []
        for year in self.bs_years:
            if year == self.bs_years[0] and str(self.bs_years[0]) == datetime.datetime.today().strftime('%Y'):
                d = datetime.datetime.today().strftime('%Y-%m-%d')
                #df = fdr.DataReader('000270',d, d)
                df = fdr.DataReader(self.stock_code,'2022-05-31', '2022-05-31')
                #print('this year : ',df['Close'][0])
            else:
                mon = 12
                day = 30
                f_day = '-12-31'
                
                d = date(int(year), mon, day)
                if d.weekday() == 6:
                    d = d-timedelta(days=2)
                elif d.weekday() == 5:
                    d = d-timedelta(days=1)

                d = d-timedelta(days=1)
                
                #print(self.stock_code)
                #print(d.strftime('%Y-%m-%d'))
                #print(str(year)+f_day)

                df = fdr.DataReader(self.stock_code,d.strftime('%Y-%m-%d'), str(year)+f_day)
                
                #print('pass year : ', df['Close'][0])

            stock_price.append(df['Close'][0])
        
        index = 0
        #stock_count
        for year in self.bs_years:
            self.total_data[year].append(stock_price[index])
            index = index+1

    def cal_mc(self):
        for year in self.bs_years:
            logger.debug(year)
            if self.total_data[year][-2] == 0:
                self.total_data[year][-2] = self.total_data[year-1][-2]
            mc = self.total_data[year][-1] * self.total_data[year][-2]
            self.total_data[year].append(mc)


    def cal_pred_val(self):
        revenu_w = []
        revenu_idx = 0
        rq_idx = 1

        income_w = []
        income_idx = 4
        iq_idx = 5
        
        cf_w = []
        cf_idx = 8
        cq_idx = 9
 

        for year in self.bs_years:
            y_revenu = self.total_data[year][revenu_idx]
            y_q = self.total_data[year][rq_idx]
            if y_revenu == 0 or y_q == 0:
                continue
            else:
                revenu_w.append(y_revenu/y_q)
                
        for year in self.bs_years:
            y_income = self.total_data[year][income_idx]
            y_q = self.total_data[year][iq_idx]
            if y_income == 0 or y_q == 0:
                continue
            elif y_income < 0 or y_q < 0:
                continue
            else:
                income_w.append(y_income/y_q)

        for year in self.bs_years:
            y_cf = self.total_data[year][cf_idx]
            y_q = self.total_data[year][cq_idx]
            if y_cf == 0 or y_q == 0:
                continue
            elif y_cf < 0 or y_q < 0:
                continue
            else:
                cf_w.append(y_cf/y_q)

        if len(income_w) == 0:
            income_w.append(4)

        if len(cf_w) == 0:
            cf_w.append(4)
        logger.debug(cf_w)

         
        if (self.total_data[self.bs_years[0]][revenu_idx]) == 0:
            self.total_data[self.bs_years[0]][revenu_idx] = self.total_data[self.bs_years[0]][rq_idx] * np.mean(revenu_w)
        
        if (self.total_data[self.bs_years[0]][income_idx]) == 0:
            self.total_data[self.bs_years[0]][income_idx] = self.total_data[self.bs_years[0]][iq_idx] * np.mean(income_w)

        if (self.total_data[self.bs_years[0]][cf_idx]) == 0:
            self.total_data[self.bs_years[0]][cf_idx] = self.total_data[self.bs_years[0]][cq_idx] * np.mean(cf_w)


    def cal_growth(self):
        r_idx = 0
        i_idx = 4
        c_idx = 8
        s_idx = 13
        m_idx = 14

        for year in self.bs_years:
            if year == self.bs_years[-1]:
                self.total_data[year].append(0)
                self.total_data[year].append(0)
                self.total_data[year].append(0)
                self.total_data[year].append(0)
                self.total_data[year].append(0)
                self.total_data[year].append(0)
                break
            
            c_revenu = self.total_data[year][r_idx]
            p_revenu = self.total_data[year-1][r_idx]
            rg = (c_revenu-p_revenu)/p_revenu
            self.total_data[year].append(rg)
            
            c_income = self.total_data[year][i_idx]
            p_income = self.total_data[year-1][i_idx]
            ig = (c_income-p_income)/p_income
            self.total_data[year].append(ig)

            c_cf = self.total_data[year][c_idx]
            p_cf = self.total_data[year-1][c_idx]
            cg = (c_cf - p_cf)/p_cf
            self.total_data[year].append(cg)

            logger.debug('{} : {}'.format(year-1, self.total_data[year-1]))
            c_stock = self.total_data[year][s_idx]
            p_stock = self.total_data[year-1][s_idx]
            sg = (c_stock-p_stock)/p_stock
            self.total_data[year].append(sg)

            c_mc = self.total_data[year][m_idx]
            p_mc = self.total_data[year-1][m_idx]
            mg = (c_mc-p_mc)/p_mc
            self.total_data[year].append(mg)

            tmp_list = [rg,ig,cg,sg,mg]
            tmp_abs_list = [abs(rg),abs(ig),abs(cg),abs(sg),abs(mg)]
            tmp = min(tmp_abs_list)
            tmp_index = tmp_abs_list.index(tmp)

            self.total_data[year].append(tmp_list[tmp_index])
            
    def cal_mc_pred(self):
        mc_idx = 14 
        min_idx = 20
        sc_idx = 12
        sp_idx = 13

        nav_list = []
        for year in reversed(self.bs_years):
            if year == list(reversed(self.bs_years))[0] or year == list(reversed(self.bs_years))[1]:
                self.total_data[year].append(0)
                self.total_data[year].append(0)
                self.total_data[year].append(0)
                self.total_data[year].append(0)
                continue

            p_mc = self.total_data[year-1][mc_idx]
            p_min = self.total_data[year-1][min_idx]
            mc = p_mc*(p_min+1)
            self.total_data[year].append(mc)

            s_cnt = self.total_data[year][sc_idx]
            p_price = mc/s_cnt
            p_nav = self.total_data[year-1][24]
            if p_nav != 0:
                p_price = p_price*p_nav

            self.total_data[year].append(p_price)
            
            price = self.total_data[year][sp_idx]
            nav = price/p_price
            self.total_data[year].append(nav)

            nav_list.append(nav)
            avr_nav = np.mean(nav_list)
            self.total_data[year].append(avr_nav)
            
    def cal_pred_price(self):
        r_idx = 0
        i_idx = 4
        c_idx = 8
        sc_idx = 12
        s_idx = 13
        m_idx = 14
        g_idx = 20
            
        pred_list = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        pred_list.append('평균')
        e_year = self.bs_years[0]
        s_year = self.bs_years[-1]

        ret_list = []

        for year in self.bs_years:
            if year == e_year:
                continue
            s_year = year
            
            s = self.total_data[s_year][r_idx]
            e = self.total_data[e_year][r_idx]
            ret = (math.pow(e/s,1/(e_year-s_year))-1)*100
            ret_list.append(ret)

        pred_list.append(np.mean(ret_list))
        print('ret : ', ret)



        """
        s = self.total_data[s_year][r_idx]
        e = self.total_data[e_year][r_idx]
        ret = (math.pow(e/s,1/(e_year-s_year))-1)*100
        pred_list.append(ret)
        print('ret : ', ret)
        """ 
            
        ret_list = []
        for year in self.bs_years:
            m_w = 1.0
            if year == e_year:
                continue
            s_year = year
            
                        
            s = self.total_data[s_year][i_idx]
            e = self.total_data[e_year][i_idx]
            if s < 0:
                e = e - s
                s = -s

            if e < 0:
                s = -s
                m_w = -1.0

            logger.debug('year : {}'.format(s_year))
            logger.debug('s : {}'.format(s))
            logger.debug('e : {}'.format(e))

            ret = (math.pow(e/s,1/(e_year-s_year))-1)*100 * m_w
            ret_list.append(ret)

        pred_list.append(np.mean(ret_list))
        print('ret : ', ret)


        """
        s = self.total_data[s_year][i_idx]
        e = self.total_data[e_year][i_idx]
        logger.debug('s income : {}'.format(s))
        logger.debug('e income : {}'.format(e))
        if s < 0:
            e = e - s
            s = -s
        ret = (math.pow(e/s,1/(e_year-s_year))-1)*100
        pred_list.append(ret)
        print('ret : ', ret)
        """

        ret_list = []
        for year in self.bs_years:
            m_w = 1.0
            if year == e_year:
                continue
            s_year = year
                        
            s = self.total_data[s_year][c_idx]
            e = self.total_data[e_year][c_idx]
            logger.debug('s : {}'.format(s))
            logger.debug('e : {}'.format(e))

            if s < 0:
                e = e - s
                s = -s

            if e < 0:
                s = -s
                m_w = -1.0
            
            logger.debug('year : {}'.format(s_year))
            logger.debug('s : {}'.format(s))
            logger.debug('e : {}'.format(e))

            ret = (math.pow(e/s,1/(e_year-s_year))-1)*100 * m_w
            ret_list.append(ret)

        pred_list.append(np.mean(ret_list))
        print('ret : ', ret)

        
        """
        s = self.total_data[s_year][c_idx]
        e = self.total_data[e_year][c_idx]
        logger.debug('s cf : {}'.format(s))
        logger.debug('e cf : {}'.format(e))
        if s < 0:
            e = e - s
            s = -s
        logger.debug('mod s cf : {}'.format(s))
        logger.debug('mod e cf : {}'.format(e))
        logger.debug('e/s : {}'.format(e/s))
        ret = (math.pow(e/s,1/(e_year-s_year))-1)*100
        pred_list.append(ret)
        print('ret : ', ret)
        """


        s = self.total_data[s_year][s_idx]
        e = self.total_data[e_year][s_idx]
        ret = (math.pow(e/s,1/(e_year-s_year))-1)*100
        pred_list.append(ret)
        print('ret : ', ret)

        s = self.total_data[s_year][m_idx]
        e = self.total_data[e_year][m_idx]
        ret = (math.pow(e/s,1/(e_year-s_year))-1)*100
        pred_list.append(ret)
        print('ret : ', ret)

        pred_list.append(0)

        mc = self.total_data[e_year][m_idx]
        g = self.total_data[e_year][g_idx]
        p_mc = mc*(1+g)
        pred_list.append(p_mc)
        print('p_mc : ', p_mc)
        

        sc = self.total_data[e_year][sc_idx]
        p_price = p_mc/sc * (self.total_data[e_year][-1])
        pred_list.append(p_price)
        pred_list.append(0)
        pred_list.append(0)
        
            
        self.total_data['Pred'] = pred_list







