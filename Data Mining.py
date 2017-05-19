from bs4 import BeautifulSoup
import re
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import zipfile
import time
import glob
import os



manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""

background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
          singleProxy: {
            scheme: "http",
            host: "us-wa.proxymesh.com",
            port: parseInt(31280)
          },
          bypassList: ["foobar.com"]
        }
      };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "XX",
            password: "XX"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
"""


pluginfile = 'proxy_auth_plugin.zip'

with zipfile.ZipFile(pluginfile, 'w') as zp:
    zp.writestr("manifest.json", manifest_json)
    zp.writestr("background.js", background_js)

co = Options()
co.add_argument("--start-maximized")
co.add_extension(pluginfile)



for year in range(1997,2017):
    for month in range(1,13): 
        for day in range(1,32): 
            # 代理服务器
            proxyHost = "us-wa.proxymesh.com"
            proxyPort = "31280"

            # 代理隧道验证信息
            proxyUser = "XX"  #proxy account registered in proxymesh
            proxyPass = "XX"

            service_args = [
                "--proxy-type=http",
                "--proxy=%(host)s:%(port)s" % {
                    "host": proxyHost,
                    "port": proxyPort,
                },
                "--proxy-auth=%(user)s:%(pass)s" % {
                    "user": proxyUser,
                    "pass": proxyPass,
                },
            ]
            proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
                "host": proxyHost,
                "port": proxyPort,
                "user": proxyUser,
                "pass": proxyPass,
            }
            proxies = {
                "http": proxyMeta,
                "https": proxyMeta,
            }

            driver = webdriver.Chrome("D:\chromedriver", chrome_options=co)
            #driver.set_page_load_timeout(50)

            row = 0
            df = pd.DataFrame(
                columns=['ID', 'Plaintiff', 'Defendant', 'Filling date', 'Calendar', 'Judge', 'Judgefinal'])
            website = 'https://courtlink.lexisnexis.com/cookcounty/FindDock.aspx?NCase=&SearchType=1&Database=3&case_no=&Year=&div=&caseno=&PLtype=1&sname=&CDate=' + str(
                month) + '%2F' + str(day) + '%2F'+str(year)
            a = requests.get(website, proxies=proxies)
            print(website)

            urlsoup = a.text

            url = re.findall(r"(?<=href=\").+?(?=\")|(?<=href=\').+?(?=\')", urlsoup)  # get url from one page
            if len(url) == 1:
                continue
            numofurl = 0
            for i in url:
                if 'Find' in i:
                    numofurl += 1
                else:
                    break
            pagenumber = len(url) - 1 - numofurl

            for s in range(pagenumber + 1):
                driver.get(website)
                # click page
                try:
                    driver.find_element_by_xpath(
                        '//*[@id="dgdCaseList"]/tbody/tr[52]/td/table/tbody/tr/td[%d]' % (s + 1)).click()
                except:
                    print("only one page")
                web_data = driver.page_source
                soup2 = BeautifulSoup(web_data, 'lxml')
                dd2 = soup2.get_text()
                while 'Host Error' in dd2:  # in case of ip block
                    test = driver.find_element_by_xpath('//*[@id="dgdCaseList"]/tbody/tr[10]/td[1]/a').text

                url = re.findall(r"(?<=href=\").+?(?=\")|(?<=href=\').+?(?=\')", web_data)
                for j in range(len(url) - 1 - pagenumber):
                    ID = driver.find_element_by_xpath('//*[@id="dgdCaseList"]/tbody/tr[%d]/td[1]/a' % (j + 2)).text
                    plaintiff = driver.find_element_by_xpath('//*[@id="dgdCaseList"]/tbody/tr[%d]/td[2]' % (j + 2)).text
                    defendant = driver.find_element_by_xpath('//*[@id="dgdCaseList"]/tbody/tr[%d]/td[3]' % (j + 2)).text
                    df.loc[row] = [ID, plaintiff, defendant, '0', '0', '0', '0']
                    row += 1
                driver.close()
                driver = webdriver.Chrome("D:\chromedriver", chrome_options=co)
                #driver.set_page_load_timeout(50)

                for i in url:
                    if 'Find' in i:  # in case it's not url

                        page = 'https://courtlink.lexisnexis.com/cookcounty/' + i
                        driver.get(page)

                        web_data = driver.page_source
                        soup = BeautifulSoup(web_data, 'lxml')
                        dd = soup.get_text()
                        #while 'Host Error' in dd: #in case of ip block with same ip proxy
                         #   driver.close()
                          #  driver = webdriver.Chrome("D:\chromedriver", chrome_options=co)
                           # driver.get(page)
                            #web_data = driver.page_source
                            #soup = BeautifulSoup(web_data, 'lxml')
                            #dd = soup.get_text()
                        # judge = driver.find_element_by_xpath('//*[@id="objCaseDetails"]/table[2]/tbody/tr[2]/td[1]').text
                        n = driver.find_element_by_xpath('//*[@id="lblBottom"]').text  # case number
                        # r = requests.get(page)
                        # n = soup.find(id='lblBottom')  # case number
                        # d = soup.find_all('td',id='objCaseDetails')  # filling date
                        if 'undefined' in dd: # in case of invalid page
                            continue
                        date = dd[106:117]
                        ca = dd.split()
                        try:
                            calendar = ca[ca.index('Calendar:') + 1]
                        except:
                            calendar=' '
                        # dfnew = pd.DataFrame({'ID': [n], 'Filling date': [date], 'Calendar': [calendar],'Judge':[judge]})
                        try:
                            judge = ca[ca.index('Judge:') + 1] + ' ' + ca[ca.index('Judge:') + 2] + ' ' + ca[
                                ca.index('Judge:') + 3]
                            judgelist = [i for i, v in enumerate(ca) if v == 'Judge:']
                            judgefinal = ca[judgelist[-1] + 1] + ' ' + ca[judgelist[-1] + 2] +' ' + ca[judgelist[-1] + 3]
                            index = list(df['ID']).index(n)
                        except:
                            index = list(df['ID']).index(n)
                            judge='nan'
                            judgefinal='nan'

                        df.loc[index]['Filling date'] = date
                        df.loc[index]['Calendar'] = calendar
                        df.loc[index]['Judge'] = judge
                        df.loc[index]['Judgefinal'] = judgefinal
                driver.close()
                driver = webdriver.Chrome("D:\chromedriver", chrome_options=co)
                #driver.set_page_load_timeout(50)

            print(df)
            df.to_csv("%dyear%dmonth%dday.csv" % (year, month, day))
            
#merge all dataset
path=r'C:\Users\nzy12\Desktop\1'
all_files=glob.glob(os.path.join(path,"*.csv"))
frame=pd.DataFrame()
df_from_each_file=(pd.read_csv(f) for f in all_files)
all_df=pd.concat(df_from_each_file,ignore_index=True)
all_df.to_csv("alldata.csv" )
