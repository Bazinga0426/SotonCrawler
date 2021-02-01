import requests
from bs4 import BeautifulSoup
import math


if __name__ == "__main__":

    header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/87.0.4280.88 Safari/537.36"}
    initUrl = 'http://localhost:8081/index'
    content = requests.get(initUrl, headers=header).text
    soup = BeautifulSoup(content, "html.parser")
    # Crawl the a tag whose current class is item-thumb bg-deepgrey
    element_lists = soup.find_all("a", class_="item-thumb bg-deepgrey")
    blog_url_lists = []
    # Loop through the tag list to get the href link information in the so-called a tag
    for element in element_lists:
        href = element.attrs['href']
        blog_url_lists.append(href)

    # Get all the content in blog_url and add it to the content_dict dictionary
    content_dicts = {}
    for blog_url in blog_url_lists:
        blog_url = "http://localhost:8081/" + str(blog_url)
        content = requests.get(blog_url, header).text
        content_dicts[blog_url] = content

    # Create two files, file_data and filecomment, respectively
    file_data = open("data.txt", "a")
    file_comment = open("comments.txt", "a")

    # Traverse the dictionary to get the url and content content
    comments_list = []  # Define the comments list to capture subsequent comment information
    for url, content in content_dicts.items():
        # Get data information
        soup = BeautifulSoup(content, "html.parser")
        title_text = soup.find(class_="post-title").find_next("a").text
        detail_text = soup.find(class_="post-data")
        time_text = detail_text.find_next("time").text
        category_text = detail_text.find_all_next("a")[0].text
        cnum_text = detail_text.find_all_next("a")[1].text
        data_info = {"title": title_text, "publish time": time_text, "category": category_text,
                     "comment num": cnum_text}
        commentDict = {"url": url, "title": title_text, "cnum_number": int(cnum_text.split(" ")[0])}
        comments_list.append(commentDict)
        # Add data_info information to file_data file
        file_data.write(str(data_info) + '\n')
    file_data.close()

    for comment in comments_list:
        urltail = comment['url']
        title_text = comment['title']
        cnum_number = comment['cnum_number']
        # Get comment url
        url_comments = []
        comment_contents = []
        for i in range(math.ceil(cnum_number / 6) + 1)[1:]:
            url_comment = urltail + "?cp=" + str(i) + "#comments"
            url_comments.append(url_comment)
            print(url_comments)
        for url_comment in url_comments:
            content = requests.get(url_comment, header).text
            soup = BeautifulSoup(content, "html.parser")
            comment_elements = soup.find_all(class_="comment-content")
            for comment_element in comment_elements:
                comment_text = comment_element.find_all("p")[1].text
                comment_contents.append(comment_text)
        comment_info = {"title": title_text, "comments": comment_contents}

        file_comment.write(str(comment_info) + "\n")
    file_comment.close()
