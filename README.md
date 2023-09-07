# Medium_Crawler_for_TWDS

> #### 專案目的：爬取 TWDS 版聚筆記文並存放至 Google Sheet 中

1. 使用前：
   - 請先更改`.env.example`內容
   - 請申請 Google Sheet API 憑證，並放置相同資料夾
3. `app.py` 為主程式，可在 for 迴圈設定爬取的「年份`Y`、月份`M`」
4. `crawler_function`：
   - `MediumPublicationCrawler` 爬取 [Publication](https://medium.com/twdsmeetup/archive) 頁面的文章網址
   - `MediumCrawler` 負責爬取文章頁面的各式資訊
