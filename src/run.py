import json
import csv
import os
import requests
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import smtplib

class Notificator:
    
    def __init__(self, setting, number):
        print ('[', number + 1, ']', setting['email'])

        self.cpo_url = 'https://cpo.lexus.jp'
        self.param  = setting['params']
        self.dealers = setting['dealers']
        self.output_file_path = 'output/' + setting['keyword'] + '.csv'

        self.current_identification = []
        self.diff_identification = []
        self.old_identification = []
        self.cars = {}

        self.get_current_infomation()

    def remove_space(self, string1):
        return string1.replace('　', '').replace('\t', '').replace('\n', '').replace('<br>', '').replace('\r', '').replace(' ', '')

    def log_carinfo(self, string1, string2, num=0):
        print(num if num != 0 else '   ', string1.ljust(8), string2)

    def get_current_infomation(self):
        page = 1
        count = 1
        while True:
        
            full_url = self.cpo_url + '/cposearch/result_list?Pg=' + str(page) + '&' + self.param
            req = requests.get(full_url)
            req.encoding = req.apparent_encoding

            soup = BeautifulSoup(req.text,"html.parser")

            table = soup.find('div', class_='result-list')

            rows = table.find_all('div', class_='result-list_item')

            for row in rows:
                car = {}

                name = row.find('h2', class_='c-result-name')
                car['name'] = self.remove_space(name.text)
                link = row.find('a')
                car['link'] = link.get('href')
                car['full_link'] = self.cpo_url + car['link']            

                tags = row.find_all('li', class_='c-page-head-tags_item')

                is_fair = False
                is_negotiation = False

                for tag in tags:
                    if tag.text == 'フェア対象車':
                        print('kiteruyo')
                        is_fair = True
                    if tag.text == '商談中':
                        is_negotiation = True

                car['is_fair'] = is_fair            
                car['is_negotiation'] = is_negotiation               

                dealer = row.find('p', class_='c-result-foot_shop')
                dealer_name = dealer.find('span', class_='u-align-items-center')
                car['dealer'] = self.remove_space(dealer_name.text)
                
                price = row.find('div', class_='c-result-price')
                car['price'] = self.remove_space(price.text) 

                result_detail =  row.find('div', class_='c-result-detail')
                result_detail_items = result_detail.find_all('dl', class_='c-result-detail_item')

                car['year'] = self.remove_space(result_detail_items[0].find('dd').text)
                car['mileage'] = self.remove_space(result_detail_items[1].find('dd').text)               
                car['inspection'] = self.remove_space(result_detail_items[2].find('dd').text)               

                color = row.find('p', class_='c-result-ruby')
                car['color'] = self.remove_space(color.text)                

                if car['is_fair'] == True and not car['dealer'] in self.dealers:
                    continue

                #車情報出力
                self.log_carinfo('車名', car['name'], f'{count:03}')
                self.log_carinfo('フェア対象車', car['is_fair'])
                self.log_carinfo('交渉中', car['is_negotiation'])
                self.log_carinfo('販売店', car['dealer'])
                self.log_carinfo('販売価格', car['price'])
                self.log_carinfo('年式', car['year'])
                self.log_carinfo('走行距離', car['mileage'])
                self.log_carinfo('車体色', car['color'])
                self.log_carinfo('車検', car['inspection'])

                self.current_identification.append(car['link'])
                self.cars[car['link']] = car

                count = count + 1

            pagination = soup.find('ul', class_='md-pager-list')
            next_button = pagination.find('li', class_='md-pager_next')
            is_continue = next_button.find('a')
            if is_continue == None:
                break
            page = page + 1

    def input_file(self):
        
        is_file = os.path.isfile(self.output_file_path)
        if not is_file:
            print('output file not found')
            return
        with open(self.output_file_path) as f:
            for row in csv.reader(f):
                self.old_identification = row

    def diff_file(self):
        self.diff_identification = set(self.current_identification) - set(self.old_identification)
            

    def output_file(self):
        with open(self.output_file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.current_identification)

    def target_cars(self):
        print(self.diff_identification)
    
    def get_diff_cars(self):
        return self.diff_identification
    
    def get_cars_detail(self):
        return self.cars
    
    def get_diff_cars_count(self):
        return len(self.diff_identification)

class Mailer:

    def __init__(self, mail_to, mail_from, mail_account, mail_password, mail_smtp, mail_port, keyword):

        self.keyword = keyword

        self.msg = MIMEMultipart()
        self.msg['Subject'] = '[新着情報] ' + self.keyword + ' - Lexus CPO 監視システム'
        self.msg['From'] = '%s <%s>'%(Header('Lexus CPO 監視システム'.encode('iso-2022-jp'),'iso-2022-jp').encode(), mail_from)
        self.msg['To'] = mail_to

        print('mail server login')
        self.server = smtplib.SMTP(mail_smtp, str(mail_port))
        self.server.login(mail_account, mail_password)

        self.body = ""

    def generate_body(self, diff_cars, cars_detail):

        self.body += "CPOに新しい車が登録されました\n追加された車の一覧は以下になります。\n\n------------------- 更新内容 --------------------\n"
        self.body += "keyword: " + self.keyword + "\n"
        for i, car in enumerate(diff_cars):
            car_detail = cars_detail[car]
            self.write_header(i, car_detail['name'])
            self.write_body('フェア対象車', str(car_detail['is_fair']))
            self.write_body('交渉中', str(car_detail['is_negotiation']))
            self.write_body('車検', car_detail['inspection'])
            self.write_body('販売店', car_detail['dealer'])
            self.write_body('販売価格', car_detail['price'])
            self.write_body('年式', car_detail['year'])
            self.write_body('走行距離', car_detail['mileage'])
            self.write_body('車体色', car_detail['color'])
            self.write_body('リンク', car_detail['full_link'])
            self.write_footer

        self.body +="------------------------------------------\n\n※このメールは送信専用アドレスです。このアドレスにご返信されても確認致しかねますのでご了承ください。\n\nこのメールはLexus CPO監視システムβ1.1により自動送信されています。\n5分毎に更新を確認し、更新を検知した場合はお知らせします。"

    def write_header(self, num, name):
        self.body += str(num + 1) + ' -- ' + name + '\n'
    
    def write_body(self, key, value):
        self.body += '     ' + key + ' : ' + value + '\n'
    
    def write_footer(self):
        self.body += "\n"

    def print_draft(self):
        print(self.body)
    
    def send_mail(self):
        self.msg.attach(MIMEText(self.body, 'plain', 'utf-8'))
        self.server.send_message(self.msg)
        self.server.quit()

def main():
    file_name = 'settingsorigin.json'

    with open(file_name) as f:
        di = json.load(f)

    print("Lexus CPO Notification System Start")
    print("version " + str(di['version']))

    for i, x in enumerate(di['settings']):
        notificator = Notificator(x, i)
        notificator.input_file()
        notificator.diff_file()
        notificator.output_file()
        notificator.target_cars()

        if notificator.get_diff_cars_count() < 1:
            print('更新はありませんでした', notificator.get_diff_cars_count())
            continue

        mailer = Mailer(
            x['email'],
            di['mail']['from'],
            di['mail']['account'],
            di['mail']['password'],
            di['mail']['smtp'],
            di['mail']['port'],
            x['keyword']
            )
        
        mailer.generate_body(notificator.get_diff_cars(), notificator.get_cars_detail())
        mailer.print_draft()
        mailer.send_mail()

if __name__ == "__main__":
    main()