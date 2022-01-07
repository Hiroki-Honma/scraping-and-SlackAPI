import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import requests

options = Options()

driver = webdriver.Chrome("./chromedriver_win32/chromedriver.exe", options=options)

#urlを指定して上で作成したdriverを用いて, websiteを開く

#スクレイピング作業を関数化
def scr(url):
    driver.get(url)
    # サーバーに負荷を書けないようにする
    #処理を2秒ごとに停止
    time.sleep(2)

    #htmlの属性名がdui-card.searchresultitemのものの情報を引きぬいてくる
    #itemsにはselenium型なる型のもののリストが作られている
    #slenium型のものは.textでテキスト情報のみ抜き取れる
    items = driver.find_elements_by_class_name("dui-card.searchresultitem")
    # print(type(items))
    # print(type(items[1]))
    # print(items[1])
    # print(items[1].text)

    item_name = []
    url_list = []
    stock_flg = []

    for item in items:
        #itemの中のtitleを取得
        title = item.find_element_by_class_name("content.title")
        item_name.append(title.text)

        #属性aから属性値hrefを取り出す
        url = item.find_element_by_tag_name("a").get_attribute("href")
        url_list.append(url)

        item = item.text
        item = item.split("\n")

        if "売り切れ" in item:
            stock_flg.append(1)
        else:
            stock_flg.append(0)

    df = pd.DataFrame([item_name, url_list, stock_flg]).T
    df.columns = ["item_name", "url", "stock_flg"]
    # print(df)

    #作業が終わったら閉じる
    driver.quit()

    return df

def slack_send(df):
    df = df.sort_values(by="stock_flg", ascending=False)
    df.to_csv("test.csv")


    #botの情報をもっている
    TOKEN="(botのToken)"
    #ワークスペースの情報をもっている
    CHANNEL = "(ワークスペースのid)"

    files = {
        "file":open("test.csv", encoding="utf8", errors='ignore')
    }

    today = datetime.date.today()
    out_of_stock_rate = df.stock_flg.sum()/len(df)

    params = {
        "token":  TOKEN,
        "channels": CHANNEL,
        "filename": f"rakuten_stock_{today}.csv",
        "initial_comment": f"楽天の在庫情報です。現在の欠品率は{out_of_stock_rate*100:.1f}%です。",
        "title" : f"rkuten_stock_{today}.csv"
    }
    requests.post(url="https://slack.com/api/files.upload", params=params, files=files)



def main():
    url = "https://search.rakuten.co.jp/search/mall/ANKER/?f=0"
    df = scr(url)
    slack_send(df)
    print(df)

#これを書いておくかないとこのパッケージをインポートしたらすぐに上で書いた関数が実行される
if __name__ == "__main__":   # 他パッケージで実行するとそのパッケージ名と一致しないのでmainが実行されない
    main()
