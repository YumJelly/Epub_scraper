import requests
from bs4 import BeautifulSoup
from ebooklib import epub
import uuid
import os
import urllib
from PIL import Image, ImageDraw, ImageFont


def draw_text(d: ImageDraw, text: str, position: tuple, font: ImageFont, max_width: int):
        words = text.split()
        lines = []
        current_line = words[0]
        for word in words[1:]:
            if d.textsize(current_line + ' ' + word, font=font)[0] <= max_width:
                current_line += ' ' + word
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        y_text = position[1]
        for line in lines:
            width, height = d.textsize(line, font=font)
            d.text((position[0], y_text), line, font=font, fill=(0, 0, 0))
            y_text += height

def scraper_for_quanben5(base_url: str, target_url: str, epub_folder_path: str, replace_book_cover: bool = True):
    
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

        book_cover_url = soup.find('div', class_='pic').find('img').get('src')
        if book_cover_url is not None and not replace_book_cover :
            print(book_cover_url)
            # Download the book cover image
            urllib.request.urlretrieve(book_cover_url, f"{epub_folder_path}{book_title}.jpg")
            book.set_cover(f"{book_title}.jpg", open(f"{epub_folder_path}{book_title}.jpg", 'rb').read())
        else:
            img = Image.new('RGB', (600, 800), color = (255, 255, 255))
            d = ImageDraw.Draw(img)
            font = ImageFont.truetype('TWSung.otf', 24)
            position = (10, 10)
            max_width = img.width - 20
            draw_text(d, book_title, position, font, max_width)
            img.save(f"{epub_folder_path}{book_title}.jpg")
            book.set_cover(f"{book_title}.jpg", open(f"{epub_folder_path}{book_title}.jpg", 'rb').read())
            print("No book cover found or you want to replace it, So I created one for you.")
        # Create the epub file
        # define CSS style
        # add default NCX and Nav file
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # add CSS file
        style = 'p {padding: 1em;\
                text-indent: 2.5em;\
                line-height: 1.6em;\
                word-break: break-all;\
                text-align: justify;\
            }'
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=style,
        )
        
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
                # chapter_content = chapter_soup.find('div', id='content').get_text() # this will get the text only
                chapter_lines = chapter_soup.find('div', id='content').find_all('p') # this will get the text with html tags
                chapter_lines = '<h2>' + chapter_name + '</h2>' + str().join(str(line) for line in chapter_lines)
                # print(chapter_lines)
                # Create a chapter
                chapter = epub.EpubHtml(title=chapter_name, file_name=f'chapter_{chapter_name}.xhtml', lang='zh')
                chapter.content = chapter_lines
                chapter.add_item(nav_css)
                # Add the chapter to the book
                book.add_item(chapter)
                book.toc.append(chapter)
                book.spine.append(chapter)

        book.add_item(nav_css)
        # write to the file
        epub.write_epub(epub_folder_path + book_title + ".epub", book, {})
        

if __name__ == '__main__':
    base_url = 'https://big5.quanben5.com'
    # change target_url to the book you want to download
    target_url = 'https://big5.quanben5.com/n/doushentianxia/xiaoshuo.html'
    epub_folder_path = './epub/'
    scraper_for_quanben5(base_url, target_url, epub_folder_path, replace_book_cover=False)