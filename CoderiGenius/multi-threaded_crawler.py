import threading
import requests
from queue import Queue
from bs4 import BeautifulSoup
import time


class ThreadCrawl(threading.Thread):
    def __init__(self, crawler, blogQueue, dataQueue, header):
        super(ThreadCrawl, self).__init__()
        self.crawler = crawler
        self.blogQueue = blogQueue
        self.dataQueue = dataQueue
        self.header = header

    def run(self):
        print("start " + self.crawler + "\n")
        while not CRAWL_EXIT:
            try:
                blog = self.blogQueue.get(block=False)
                url = "http://localhost:8081/" + str(blog)
                content = requests.get(url, self.header).text
                self.dataQueue.put(content)
            except:
                pass
        print("end " + self.crawler + "\n")


class ThreadParse(threading.Thread):
    def __init__(self, parser, dataQueue, file, lock):
        super(ThreadParse, self).__init__()
        self.parser = parser
        self.dataQueue = dataQueue
        self.file = file
        self.lock = lock

    def run(self):
        print("start " + self.parser + "\n")
        while not PARSE_EXIT:
            try:
                data = self.dataQueue.get(block=False)
                soup = BeautifulSoup(data, "html.parser")
                title = soup.find(class_="post-title").find_next("a").text
                data = soup.find(class_="post-data")
                ptime = data.find_next("time").text
                category = data.find_all_next("a")[0].text
                cnum = data.find_all_next("a")[1].text
               # print(soup.find(class_='comment-list').find("li"))
                commentList = []
                for comment in soup.find(class_='comment-list').findAll("li"):
                    author = comment.find(class_="comment-author").text.replace("\n","")
                    commentText = comment.find(class_="comment-content").text.replace("\n","")
                    commnetTime = comment.find(class_="comment-time").text.replace("\n","")
                    commentEntity = {"author":author,"content":commentText,"time":commnetTime}
                    print(commentEntity)
                    commentList.append(commentEntity)

                info = {"title": title, "public time": ptime, "category": category, "comment number": cnum,"comments":commentList}
                with self.lock:
                    self.file.write(str(info) + "\n")
            except:
                pass
        print("end " + self.parser + "\n")


if __name__ == "__main__":

    CRAWL_EXIT = False
    PARSE_EXIT = False

    header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/87.0.4280.88 Safari/537.36"}

    blogQueue = Queue()
    blogList = []
    rootUrl = "http://localhost:8081/index"
    rootContent = requests.get(rootUrl, headers=header).text

    rootSoup = BeautifulSoup(rootContent, "html.parser")
    searches = rootSoup.find_all("a", class_="item-thumb bg-deepgrey")
    for search in searches:
        href = search.attrs["href"]
        blogList.append(href)

    for blogUrl in blogList:
        blogQueue.put(blogUrl)

    dataQueue = Queue()

    file = open("comments.txt", "a")
    #file = open("data.txt", "a")

    lock = threading.Lock()

    crawlList = ["crawler 1", "crawler 2", "crawler 3", "crawler 4", "crawler 5"]

    crawlThreadList = []

    for crawler in crawlList:
        thread = ThreadCrawl(crawler, blogQueue, dataQueue, header)
        thread.start()
        crawlThreadList.append(thread)

    while not blogQueue.empty():
        pass

    CRAWL_EXIT = True

    for crawlThread in crawlThreadList:
        crawlThread.join()

    print("blogQueue is empty, crawlThreads terminate")

    parseList = ["parser 1", "parser 2", "parser 3", "parser 4", "parser 5"]

    parseThreadList = []

    for parser in parseList:
        thread = ThreadParse(parser, dataQueue, file, lock)
        thread.start()
        parseThreadList.append(thread)

    while not dataQueue.empty():
        pass

    PARSE_EXIT = True

    for parseThread in parseThreadList:
        parseThread.join()

    print("dataQueue is empty, parseThreads terminate")

    with lock:
        file.close()

    print("##### end of program #####")
