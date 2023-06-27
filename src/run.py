import json
import csv
import os
import requests
from bs4 import BeautifulSoup

class Notificator:
    
    def __init__(self, setting, number):
        print ('[', number + 1, ']', setting['email'])

        self.cpo_url = 'https://cpo.lexus.jp'
        self.full_url = self.cpo_url + '/cposearch/result_list?' + setting['params']
        self.setting = setting
        self.output_file_path = 'output/' + self.setting['keyword'] + '.csv'

        self.current_identification = []
        self.diff_identification = []
        self.old_identification = []
        self.cars = []

        self.get_current_infomation()

    def remove_space(self, string1):
        return string1.replace('　', '').replace('\t', '').replace('\n', '').replace('<br>', '').replace('\r', '').replace(' ', '')

    def log_carinfo(self, string1, string2, num=0):
        print(num if num != 0 else '   ', string1.ljust(8), string2)

    def get_current_infomation(self):
        req = requests.get(self.full_url)
        req.encoding = req.apparent_encoding

        soup = BeautifulSoup(req.text,"html.parser")

        table = soup.find('table', id='table-result')

        rows = table.find_all('tbody')

        for j, row in enumerate(rows):
            car = {}

            name = row.find('a', class_='row-link')
            car['name'] = self.remove_space(name.text)
            car['link'] = name.get('href')
            car['full_link'] = self.cpo_url + car['link']
            self.log_carinfo('車名', car['name'], f'{j + 1:03}')

            fair = row.find('li', class_='fair')
            if fair == None:
                is_fair = False
            else:
                is_fair = True
            car['is_fair'] = is_fair
            self.log_carinfo('安全保障', car['is_fair'])

            dealer = row.find('span', class_='dealer')
            car['dealer'] = self.remove_space(dealer.text)
            self.log_carinfo('販売店', car['dealer'])

            price = row.find('td', class_='base-price pc-cell')
            car['price'] = self.remove_space(price.text)
            self.log_carinfo('販売価格', car['price'])

            model_year = row.find('td', class_='model-year pc-cell')
            car['year'] = self.remove_space(model_year.text)
            self.log_carinfo('年式', car['year'])

            mileage = row.find('td', class_='mileage pc-cell')
            car['mileage'] = self.remove_space(mileage.text)
            self.log_carinfo('走行距離', car['mileage'])

            color = row.find('td', class_='body-color pc-cell')
            car['color'] = self.remove_space(color.text)
            self.log_carinfo('車体色', car['color'])

            self.current_identification.append(car['link'])
            self.cars.append(car)

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






def main():
    file_name = 'settingsorigin.json'

    with open(file_name) as f:
        di = json.load(f)

    print("Lexus CPO Notification System Start")
    print("version " + str(di['version']))

    for i, x in enumerate(di['settings']):
        a = Notificator(x, i)
        a.input_file()
        a.diff_file()
        a.output_file()

        



if __name__ == "__main__":
    main()