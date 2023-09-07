import re
import requests
import json
from bs4 import BeautifulSoup

import html2text
h = html2text.HTML2Text()
h.body_width = 0  # 設為 0 不換行

# 取出連結
def urlFinder(msg):
    url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', msg)
    return url


class MediumPublicationCrawler:
    def __init__(self, url:str): 
        res = requests.get(url)
        self.soup = BeautifulSoup(res.text, 'html.parser')  

    ########## check link exists ##########
    def check_page(self, current_url):
        page_link = self.soup.find("link", rel="canonical")['href']
        print(page_link)
        return page_link == current_url

    ########## id ##########
    def get_articles_id(self):
        article_resource = self.soup.find_all(
            'div', "postArticle postArticle--short js-postArticle js-trackPostPresentation js-trackPostScrolls")
        
        articles_id = []
        for i in range(len(article_resource)):
            find_id_1 = article_resource[i].find('a', 'link link--darken')['href']
            find_id_2 = (find_id_1.split('/'))[-1]

            match = re.match(r'^(.*?)(?=\?)', find_id_2)
            if match:
                result = match.group(1)
                # print('with ugly href',result)
                final_result = re.split('-', result)  # got the article id
                article_id = final_result[-1]
                articles_id.append(article_id)

            else:
                print('result not found')
        return articles_id

    ########## img ##########
    def get_article_img(self):
        #img_lib = []
        img_sources = self.soup.find_all('img', 'graf-image')
        i = len(img_sources)
        for item in range(i):
            return img_sources[item]['src']

    ########## name ##########
    def get_article_name(self):
        name_sources = self.soup.find_all('h3')
        whole_names = (name_sources[0])
        name = whole_names.get_text()
        # result = name_text.split(']')[1]
        # name = ''.join(result.split())
        return name


class MediumCrawler:
    def __init__(self, url:str): 
        res = requests.get(url)
        self.url = url
        self.soup = BeautifulSoup(res.text, 'html.parser')    
    
    ########## content ##########
    # 取得 Markdown 格式內文
    def get_content(self):  
        article_with_markdown = self.get_markdown_content()
        article_with_markdown = self.clean_link_tags(article_with_markdown)
        article_with_markdown = self.clean_bookmark(article_with_markdown)
        return article_with_markdown  

    # 取得 Markdown 格式內文
    def get_markdown_content(self):    
        article =  self.soup.find("article")
        publication_info =  article.find(class_="speechify-ignore ab co")
        source =  article.find_all("source", "data-testid"=="og")[::2]
        img =  article.find_all("img")[2:]

        # 將發佈人資訊拿掉
        article = str(article).replace(str(publication_info),"")

        # 處理圖片部分
        source_url = []
        for i in range(len(source)):
            last_url = urlFinder(source[i]["srcset"])[-1]
            source_url.append(last_url)

        for i in range(len(img)):
            target = str(img[i])
            target_url = target.replace('/>', f' src="{source_url[i]}"/>')
            article = str(article).replace(str(img[i]),target_url,1)

        article_with_markdown = h.handle(f'{article}').lstrip()
        return article_with_markdown

    # Medium 內建連結轉換－連結標記（包括帳號）
    def clean_link_tags(self, article):    
        link_tags = re.findall("\[\n*[^\]]+\]\([^\)]+\)", article)
        clean_link_tags = []

        for tag in link_tags:
            tag = tag.replace("](/", "](https://medium.com/")
            clean_link_tags.append(tag)

        for i in range(len(link_tags)):
            article = article.replace(link_tags[i], clean_link_tags[i]) 

        return article

    # Medium 內建連結轉換－內建書籤
    def clean_bookmark(self, article):    
        bookmarks = re.findall("\[\n*## [^\]]+\]\([^\)]+\)", article)
        clean_bookmarks = []

        for bookmark in bookmarks:

            clean_bookmark = re.sub(r'\n*', '', bookmark)

            bookmark_title = re.search("##[^\]]+###",clean_bookmark)[0].replace("#","")[1:]
            clean_bookmark  = re.sub(r'\[[^\]]+\]', "[📎 "+bookmark_title+"]", clean_bookmark)
            
            clean_bookmarks.append(clean_bookmark)

        for i in range(len(bookmarks)):
            article = article.replace(bookmarks[i], clean_bookmarks[i]) 
        return article

    ########## author_info ##########
    def get_author_info(self):
        article = self.get_markdown_content()
        author = re.findall("[\u4e00-\u9fa5A-Za-z0-9\s.’_-]+[\||｜][\u4e00-\u9fa5A-Za-z0-9\s.’_-]+[＠|@][\u4e00-\u9fa5A-Za-z0-9\s.’_-]+", article)
        author_info = {
            "name" : "",
            "jobTitle" : "",
            "company" : ""
        }
        if len(author) != 0:
            author = re.split("\||｜",author[0])
            author_info["name"] = author[0]
            author_info["jobTitle"] = author[1]
            # author_info["company"] = author[2]
        
        return author_info
        
    ########## author_info ##########
    def get_keyword_tag(self):
        keyword_tag = self.soup.find_all("div", class_="ab ca")

        selected_keyword_tag = []
        for i in range(len(keyword_tag)):
            selected_keyword_tag += keyword_tag[i].find_all("a")
        selected_keyword_tag

        keyword_list = []
        for i in range(len(selected_keyword_tag)):
            single = selected_keyword_tag[i]["href"]
            single_keyword = re.findall("/tag/.*\?", single)
            if len(single_keyword) > 0:
                keyword_list.append(single_keyword[0][5:-1])

        while len(keyword_list) < 3:
            keyword_list.append("")

        return keyword_list


    ########## seo_structured_data ##########
    def get_structured_data(self):
        seo_structured_data = self.soup.find("script", type="application/ld+json").text
        seo_structured_data = json.loads(seo_structured_data)

        if type(seo_structured_data["image"]) == dict:
            seo_structured_data["image"] = seo_structured_data["image"]["url"]
        elif seo_structured_data["image"] == None:
            seo_structured_data["image"] = ""
        else:
            seo_structured_data["image"] = seo_structured_data["image"][0]

        return seo_structured_data
    
    ########## meta_tag ##########
    def get_meta_tag(self):
        meta_tag = {
            "og_type"  : self.soup.find("meta", property="og:type")["content"],
            "og_title" : self.soup.find("meta", property="og:title")["content"],
            "og_description" : self.soup.find("meta", property="og:description")["content"],
            "og_url" : self.soup.find("meta", property="og:url")["content"],
            "og_site_name" : self.soup.find("meta", property="og:site_name")["content"],
            "og_image" : self.soup.find("meta", property="og:image")["content"] if self.soup.find("meta", property="og:image") else ""
        }
        return meta_tag

    ########## articles_info ##########
    def get_articles_info(self):
        articles_info = {
            "@context" : "https://schema.org",
            "@type" : "Article",
            "id" : self.url.split("/")[-1],
            "headline" : self.get_structured_data()["headline"],
            "name" : self.get_structured_data()["name"],
            "description" : self.get_structured_data()["description"],
            "content" : self.get_content(),
            "url" : self.url,
            "about.@type" : "",
            "about.name" : "",
            "about.url" : "",
            "keywords.0" : self.get_keyword_tag()[0],
            "keywords.1" : self.get_keyword_tag()[1],
            "keywords.2" : self.get_keyword_tag()[2],
            "image.0" : self.get_structured_data()["image"],
            "author0.@type" : self.get_structured_data()["author"]["@type"],
            "author0.name" : self.get_author_info()["name"],
            "author0.url" : "",
            "author0.jobTitle" : self.get_author_info()["jobTitle"],
            "author1.@type" : self.get_structured_data()["author"]["@type"],
            "author1.name" : self.get_structured_data()["author"]["name"],
            "author1.url" : self.get_structured_data()["author"]["url"],
            "author1.jobTitle" : "",
            "author2.@type" : "",
            "author2.name" : "",
            "author2.url" : "",
            "author2.jobTitle" : "",
            "dateCreated" : self.get_structured_data()["dateCreated"],
            "datePublished" : self.get_structured_data()["datePublished"],
            "dateModified" : self.get_structured_data()["dateModified"],
            "publisher.@type": self.get_structured_data()["publisher"]["@type"],
            "publisher.name": self.get_structured_data()["publisher"]["name"],
            "publisher.url": self.get_structured_data()["publisher"]["url"],
            "publisher.logo.@type": self.get_structured_data()["publisher"]["logo"]["@type"],
            "publisher.logo.url": self.get_structured_data()["publisher"]["logo"]["url"],
            "publisher.url": self.get_structured_data()["publisher"]["url"],
            "og:type" : self.get_meta_tag()["og_type"],
            "og:title" : self.get_meta_tag()["og_title"],
            "og.description" : self.get_meta_tag()["og_description"],
            "og.url" : self.get_meta_tag()["og_url"],
            "og:site_name" : self.get_meta_tag()["og_site_name"],
            "og:image" : self.get_meta_tag()["og_image"]
        }
        return articles_info