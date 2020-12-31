import threading
import requests
from queue import Queue
from bs4 import BeautifulSoup
import math
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
                dataDict = {"url": blog, "content": content}
                self.dataQueue.put(dataDict)
            except:
                pass
        print("end " + self.crawler + "\n")


class ThreadParse(threading.Thread):
    def __init__(self, parser, dataQueue, commentQueue, file1, lock1):
        super(ThreadParse, self).__init__()
        self.parser = parser
        self.dataQueue = dataQueue
        self.commentQueue = commentQueue
        self.file1 = file1
        self.lock1 = lock1

    def run(self):
        print("start " + self.parser + "\n")
        while not PARSE_EXIT:
            try:
                data = self.dataQueue.get(block=False)
                url = data["url"]
                content = data["content"]
                soup = BeautifulSoup(content, "html.parser")
                title = soup.find(class_="post-title").find_next("a").text
                detail = soup.find(class_="post-data")
                ptime = detail.find_next("time").text
                category = detail.find_all_next("a")[0].text
                cnum = detail.find_all_next("a")[1].text
                commentDict = {"url": url, "title": title, "cnum": int(cnum.split(" ")[0])}
                self.commentQueue.put(commentDict)
                info = {"title": title, "publish time": ptime, "category": category, "comment num": cnum}
                with self.lock1:
                    self.file1.write(str(info) + "\n")
            except:
                pass
        print("end " + self.parser + "\n")


class CommentThread(threading.Thread):
    def __init__(self, commenter, commentQueue, header, file2, lock2):
        super(CommentThread, self).__init__()
        self.commenter = commenter
        self.commentQueue = commentQueue
        self.header = header
        self.file2 = file2
        self.lock2 = lock2

    def run(self):
        print("start " + self.commenter + "\n")
        while not COMMENT_EXIT:
            try:
                comment = commentQueue.get(block=False)
                urlTail = comment["url"]
                title = comment["title"]
                cnum = comment["cnum"]
                urlList = []
                cList = []
                for i in range(math.ceil(cnum / 6) + 1)[1:]:
                    url = "http://localhost:8081/" + urlTail + "?cp=" + str(i) + "#comments"
                    urlList.append(url)
                for url in urlList:
                    content = requests.get(url, self.header).text
                    soup = BeautifulSoup(content, "html.parser")
                    results = soup.find_all(class_="comment-content")
                    for result in results:
                        c = result.find_all("p")[1].text
                        cList.append(c)
                info = {"title": title, "comments": cList}
                with self.lock2:
                    self.file2.write(str(info) + "\n")
            except:
                pass
        print("end " + self.commenter + "\n")


if __name__ == "__main__":

    CRAWL_EXIT = False
    PARSE_EXIT = False
    COMMENT_EXIT = False

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

    file1 = open("data.txt", "a")
    file2 = open("comments.txt", "a")

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

    print("blogQueue is empty, crawlThreads terminate \n")

    commentQueue = Queue()

    parseList = ["parser 1", "parser 2", "parser 3", "parser 4", "parser 5"]

    parseThreadList = []

    lock1 = threading.Lock()

    for parser in parseList:
        thread = ThreadParse(parser, dataQueue, commentQueue, file1, lock1)
        thread.start()
        parseThreadList.append(thread)

    while not dataQueue.empty():
        pass

    PARSE_EXIT = True

    for parseThread in parseThreadList:
        parseThread.join()

    print("dataQueue is empty, parseThreads terminate \n")

    commenterList = ["commenter 1", "commenter 2", "commenter 3", "commenter 4", "commenter 5"]

    commentThreadList = []

    lock2 = threading.Lock()

    for commenter in commenterList:
        thread = CommentThread(commenter, commentQueue, header, file2, lock2)
        thread.start()
        commentThreadList.append(thread)

    while not commentQueue.empty():
        pass

    COMMENT_EXIT = True

    for commentThread in commentThreadList:
        commentThread.join()

    print("commentQueue is empty, commentThreads terminate \n")

    with lock1:
        file1.close()

    with lock2:
        file2.close()

    print("##### end of program #####")
