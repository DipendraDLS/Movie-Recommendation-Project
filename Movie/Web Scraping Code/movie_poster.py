import csv
import urllib.request
from bs4 import BeautifulSoup

row_names = ['movie_id', 'movie_url', 'movie_title', 'movie_genre']
with open('movie_url.csv', 'r', newline='') as in_csv:
    reader = csv.DictReader(in_csv, fieldnames=row_names, delimiter=',')
    for row in reader:
        movie_id = row['movie_id']
        movie_url = row['movie_url']
        movie_title = row['movie_title']
        movie_genre = row['movie_genre']
        domain = 'http://www.imdb.com'
        with urllib.request.urlopen(movie_url) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')
            # Get url of poster image
            try:
                imdb_rating = soup.find('strong').text
                year = soup.find('span', {'id': 'titleYear'}).find('a').get_text()
                image_url = soup.find('div', class_='poster').a.img['src']

                
                extension = '.jpg'
                image_url = ''.join(image_url.partition('_')[0])+extension
                filename = 'img/' + movie_title+extension
                with urllib.request.urlopen(image_url) as response:
                    with open(filename, 'wb') as out_image:
                        out_image.write(response.read())
                    with open('movie_poster.csv', 'a', newline='') as out_csv:
                        writer = csv.writer(out_csv, delimiter=',')
                        writer.writerow([movie_id, movie_title, imdb_rating, year, movie_genre])
            # Ignore cases where no poster image is present
            # except AttributeError:
            #     pass
            except:
                pass