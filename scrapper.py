import requests
from bs4 import BeautifulSoup
from ebooklib import epub
import uuid
import os

def scraper_for_quanben5(base_url: str, target_url: str, epub_folder_path: str):
    
    # Create a folder to store the epub files
    if not os.path.exists(epub_folder_path):
        os.makedirs(epub_folder_path)

    # Custom headers using a browser user-agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    # Send a GET request to the URL
    response = requests.get(target_url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        response.encoding = 'big5'
        # Parse the content of the response using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        book_title = soup.find('h3').get_text()
        print(book_title)
        author_name = soup.find('p', class_='info').find('span', class_='author').get_text()
        print(author_name)  
        book_description = soup.find('p', class_='description').get_text()
        print(book_description)
        li_elements = soup.find_all('li', class_='c3')
        print(f"Number of chapters: {len(li_elements)}")
        # Create an epub file
        book = epub.EpubBook()
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(book_title)
        book.set_language('zh')
        book.add_author(author_name)
        book.add_metadata('DC', 'description', book_description)

        c = 0
        # Add chapters to the epub file
        for li in li_elements:
            c += 1
            chapter_name = li.get_text()
            chapter_link = li.find('a').get('href')
            print(f"({c}/{len(li_elements)})Scrapping: Chapter name: {chapter_name}, Chapter link: {chapter_link}")
            # read the chapter content
            full_chapter_link = base_url + chapter_link
            # Send a GET request to the chapter link
            chapter_response = requests.get(full_chapter_link, headers=headers)
            # Check if the request was successful
            if chapter_response.status_code == 200:
                chapter_response.encoding = 'big5'
                # Parse the content of the response using BeautifulSoup
                chapter_soup = BeautifulSoup(chapter_response.content, 'html.parser')
                # Find the chapter content
                chapter_content = chapter_soup.find('div', id='content').get_text()
                # Create a chapter
                chapter = epub.EpubHtml(title=chapter_name, file_name=f'chapter_{chapter_name}.xhtml', lang='en')
                chapter.content = chapter_content
                # Add the chapter to the book
                book.add_item(chapter)
                book.toc.append(chapter)
                book.spine.append(chapter)
        # Create the epub file
        epub.write_epub(epub_folder_path + book_title + ".epub", book, {})
    else:
        print(f"Failed to retrieve the webpage: Status code {response.status_code}")

if __name__ == '__main__':
    base_url = 'https://big5.quanben5.com'
    # change target_url to the book you want to download
    target_url = 'https://big5.quanben5.com/n/doushentianxia/xiaoshuo.html'
    epub_folder_path = './epub/'
    scraper_for_quanben5(base_url, target_url, epub_folder_path)