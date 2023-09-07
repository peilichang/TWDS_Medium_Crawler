import os, sys, traceback
import pygsheets
import pandas as pd
from dotenv import load_dotenv
from crawler_function import MediumPublicationCrawler, MediumCrawler

try:
    load_dotenv()
    gc = pygsheets.authorize(service_account_file=os.environ["SERVICE_ACCOUNT_FILE_NAME"])

    # Google Sheet Url
    sheet_url = os.environ["GOOGLE_SHEET_URL"]
    sh = gc.open_by_url(sheet_url)
    # Google Sheet Title
    sheet = sh.worksheet_by_title(os.environ["GOOGLE_SHEET_TITLE"]) 
    medium_articles_df = sheet.get_as_df(start='A2', empty_value='', include_tailing_empty=False) 

except Exception as err:
    print(f"Unexpected {err=}, {type(err)=}")


try:
    for Y in range(2020, 2024):
        for M in range(1, 13):
            if M < 10:
                publication_url = 'https://medium.com/twdsmeetup/archive/' + str(Y) + '/0' + str(M)
            else:
                publication_url = 'https://medium.com/twdsmeetup/archive/' + str(Y) + '/' + str(M)

            medium_publication = MediumPublicationCrawler(url = publication_url)

            if not medium_publication.check_page(publication_url):
                print("頁面不存在：" + publication_url)
                continue

            articles_id = medium_publication.get_articles_id()
            print(articles_id)
            for id in articles_id:
                url  = "https://medium.com/p/" + id
                medium = MediumCrawler(url = url)

                medium_articles_column = medium_articles_df.columns.to_list()
                # print(medium.get_structured_data()["image"])
                articles_info = medium.get_articles_info()
                each_article = []
                # 取得df欄位名稱並在articles_info取得對應的值
                for col_name in medium_articles_column:
                    each_article.append(articles_info[col_name])
                
                # 確認有無重複文章
                duplicated_row = medium_articles_df[medium_articles_df["id"]==id]
                if len(duplicated_row) == 0:
                    new_article_df = pd.DataFrame([each_article], columns=medium_articles_column)
                    medium_articles_df = pd.concat([medium_articles_df, new_article_df], axis=0, ignore_index=True)
                    sheet.append_table(values=[each_article]) 
                    print(f"Append article [{id}] successfully")

                else:
                    # 若 id 已存在就不再抓其他資料
                    print(f"Article [{id}] exists")

                    # # 要進一步比對是否更新
                    # if articles_info == duplicated_row.to_dict('records')[0]:
                    #     print(f"Article [{id}] exists")
                    # else:
                    #     index = duplicated_row.index[0]
                    #     sheet.update_row(index + 3, values=[each_article])
                    #     medium_articles_df.loc[index] = each_article
                    #     print(f"Update article [{id}] successfully")


except OSError as err:
    print("OS error:", err)
except Exception as e:
    # print(f"Unexpected {err=}, {type(err)=}")
    error_class = e.__class__.__name__ #取得錯誤類型
    detail = e.args[0] #取得詳細內容
    cl, exc, tb = sys.exc_info() #取得Call Stack
    lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
    fileName = lastCallStack[0] #取得發生的檔案名稱
    lineNum = lastCallStack[1] #取得發生的行號
    funcName = lastCallStack[2] #取得發生的函數名稱
    errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
    print(errMsg)


