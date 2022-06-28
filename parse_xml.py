import xml.etree.ElementTree as ET

def parse_xml(stock_name):
    root = ET.parse('CORPCODE.xml').getroot()
    tag = root.findall('list')

    corp_code = ''

    for data in tag:
        if data[1].text == stock_name:
            if data[2].text == ' ':
                continue
            print(data[1].text+'\t'+data[2].text)
            corp_code = data[0].text
            break

    return corp_code

f = open('investing', 'r')

for data in f.readlines():
    parse_xml(data.split('\n')[0])
    
#parse_xml('카카오')



