from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import requests
import datetime
from flask import Flask,request,render_template,jsonify

# スクレピングの関数
def scr(url):
    ##スクレイピングの準備
    options = Options()
    # options.add_argument('--headless')
    # driver = webdriver.Chrome("{ご自身のディレクトリ}chromedriver.exe", options=options)
    driver = webdriver.Chrome(options=options)
    # 楽天の商品一覧
    driver.get(url)
    time.sleep(2)
    
    item_name = []
    url_list = []
    stock_flg = []

    #商品1つ1つの要素取得
    items = driver.find_elements_by_class_name('searchresultitem')
    
    #それぞれの要素から商品名と在庫切れかどうかとURLを取得
    for item in items:

        title = item.find_element_by_class_name('title')
        item_name.append(title.text)

        url = item.find_element_by_tag_name("a").get_attribute("href")
        url_list.append(url)

        item = item.text
        item = item.split("\n")

        if "売り切れ" in item:
            stock_flg.append(1)
        else:
            stock_flg.append(0)
    
    #     データフレーム化
    df = pd.DataFrame([item_name, url_list, stock_flg]).T
    df.columns = ["item_name", "url", "stock_flg"]  

    driver.quit()

    return df

# Slackにデータを送る関数
def slack_Send(df):
    #  データを在庫切れが上に来るようにソート
    df = df.sort_values(by='stock_flg', ascending=False)
    #  CSV化
    df.to_csv("test.csv")
    
    #  SLACK＿BOTのトークン
    TOKEN = "{ご自身のBOTS　API　TOKEN}"
    CHANNEL = "{ご自身のCHANNEL ID}"
    
    #     作成したファイルをオープン
    files = {
        "file" : open("test.csv")
    }
    
    today = datetime.date.today()
    out_of_stock_rate = df.stock_flg.sum()/len(df)

    params = {
        'token':TOKEN,
        'channels':CHANNEL,
        'filename': f"rakuten_stock_{today}.csv",
        'initial_comment': f"楽天の在庫情報です.欠品率は{out_of_stock_rate*100:.1f}%です",
        'title': f"rakuten_stock_{today}.csv"
    }
    requests.post(url="https://slack.com/api/files.upload",params=params, files=files)

# 実行部分
# def main():
#     url = "https://search.rakuten.co.jp/search/mall/ANKER/?f=0"
#     df = scr(url)
#     print(df)
#     slack_send(df)

#Flaskの設定
app = Flask(__name__)

@app.route("/")
def check():
    # htmlファイルをレンダリング
    return render_template('index.html')

@app.route('/output', methods=['POST'])
def output():
    #json形式でURLを受け取る
    url = request.json['url1']
    df = scr(url)
    print(df)
    out_of_stock_rate = df.stock_flg.sum()/len(df)
    print(out_of_stock_rate)
    return_data = {"result":round(out_of_stock_rate*100,1)}
    return jsonify(ResultSet=return_data)

if __name__ == "__main__":
    app.run()