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
    for word, count in word_counts.items():
        if debug:
            print(f"{word}: {count}")

        cur.execute(f"select count(*) as count from words where word = '{word}'")
        if cur.fetchone()['count'] == 0:
            cur.execute(f"INSERT INTO words (word) VALUE ('{word}')")
            word_id = cur.lastrowid
            if debug:
                print(f"Word '{word}' not found, inserting a new record, ID: {word_id}")
        else:
            cur.execute(f"select id from words where word = '{word}'")
            word_id = cur.fetchone()['id']
            if debug:
                print(f"Word '{word}' found, ID: {word_id}")

        cur.execute(f"select count(*) as count from word_count where word_id = {word_id} and url_id = {url_id}")
        if cur.fetchone()['count'] == 0:
            cur.execute(f"INSERT INTO word_count (word_id, url_id, count) VALUE ({word_id}, {url_id}, {count})")
            if debug:
                print(f"Relationship word_id: {word_id} url_id: {url_id} not found inserting a new record")
        else:
            cur.execute(
                f"UPDATE word_count SET count = {count} WHERE word_id = {word_id} AND url_id = {url_id}"
            )
            if debug:
                print(f"Relationship word_id: {word_id} url_id: {url_id} found")


if __name__ == "__main__":
    debug = False  # Set this to True to enable debug output

    db_config = {
        'user': getenv("MARIADB_USERNAME"),
        'password': getenv("MARIADB_PASSWORD"),
        'host': getenv("MARIADB_HOST"),
        'database': 'cyberminer',
        'raise_on_warnings': True,
        'autocommit': True
    }

    conn = mysql.connector.connect(**db_config)
    try:
        cursor = conn.cursor(dictionary=True)

        urls = get_urls_to_scrape(cursor, limit=100)
        while len(urls) > 0:
            for url in urls:
                word_count = buildDictFromURL(url['path'])
                if debug:
                    print(f"{word_count}\n")
                insert_word_counts(cursor, url['id'], word_count)
            urls = get_urls_to_scrape(cursor, limit=100)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
