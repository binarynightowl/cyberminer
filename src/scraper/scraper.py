import requests
from bs4 import BeautifulSoup
from bs4.element import Comment
import mysql.connector
from mysql.connector import errorcode
from os import getenv


def retrieveText(URL):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()  # rip it out

    # get text
    # text = "".join([ p.get_text() for p in soup.find_all('p') ])
    text = soup.get_text()
    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    text = text.replace("\n", " ").strip().lower()
    # before adding to DB, we can add 2 versions of the text, one without (replaced by spaces) ","", -, /, (), ?, ! and one with them, so search becomes consistent
    return text


def addWordToDict(word_counts, word):
    if word in word_counts:
        word_counts[word] += 1
    else:
        word_counts[word] = 1


def buildWordCountDict(text):
    dual_characters = [",", "-", "/", "(", "?", "!", "."]

    word_counts = {}
    for w in text.split():
        addWordToDict(word_counts, w)

        for d in dual_characters:
            if d in w:
                if d == "(":
                    # add without parenthesis
                    w2 = w.replace("(", " ").replace(")", " ")
                    addWordToDict(word_counts, w2)
                else:
                    wordSplitBySpecials = w.split(d)
                    for splittedWord in wordSplitBySpecials:
                        addWordToDict(word_counts, splittedWord)

    return word_counts


def buildDictFromURL(URL):
    text = retrieveText(URL)
    word_counts = buildWordCountDict(text)
    return word_counts


def get_urls_to_scrape(cur, limit=1000):
    query = \
        f"""SELECT u.id, u.path
           FROM urls u
                    LEFT JOIN word_count wc ON u.id = wc.url_id
           WHERE wc.id IS NULL ORDER BY id LIMIT {limit}"""

    cur.execute(query)
    return cursor.fetchall()


def insert_word_counts(cur, url_id, word_counts):
    # TODO: Actually implement the inserts here
    for word, count in word_counts.items():
        if debug:
            print(f"{word}: {count}")


if __name__ == "__main__":
    debug = False  # Set this to True to enable debug output

    db_config = {
        'user': getenv("MARIADB_USERNAME"),
        'password': getenv("MARIADB_PASSWORD"),
        'host': getenv("MARIADB_HOST"),
        'database': 'cyberminer',
        'raise_on_warnings': True,
    }

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    urls = get_urls_to_scrape(cursor)
    for url in urls:
        word_count = buildDictFromURL(url['path'])
        if debug:
            print(f"{word_count}\n")
        insert_word_counts(cursor, url['id'], word_count)
