import requests
from bs4 import BeautifulSoup
import re
import time
import mysql.connector
from mysql.connector import errorcode
from os import getenv


def get_links(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for request errors
    except requests.RequestException as e:
        if debug:
            print(f"Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    links = set()

    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        if re.match(r'http[s]?://', href):  # Filter for http/https links
            links.add(href)

    return links


def insert_domain(cursor, domain):
    cursor.execute("INSERT INTO domains (domain_name) VALUES (%s) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)",
                   (domain,))
    return cursor.lastrowid


def insert_url(cursor, domain_id, path, depth):
    cursor.execute(
        "INSERT INTO urls (domain_id, path, depth) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)",
        (domain_id, path, depth))
    return cursor.lastrowid


def get_domain_id(cursor, domain):
    cursor.execute("SELECT id FROM domains WHERE domain_name = %s", (domain,))
    result = cursor.fetchone()
    return result[0] if result else None


def get_urls_to_crawl(cursor):
    cursor.execute("SELECT path, depth FROM urls WHERE depth >= 1 ORDER BY depth")
    return cursor.fetchall()


def update_url_depth(cursor, url, new_depth):
    cursor.execute("UPDATE urls SET depth = %s WHERE path = %s", (new_depth, url))


def crawl(db_config, debug=False):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        to_crawl = get_urls_to_crawl(cursor)
        crawled = set()

        while to_crawl:
            new_to_crawl = set()

            for url, current_depth in to_crawl:
                if url not in crawled:
                    links = get_links(url)
                    domain = re.match(r'http[s]?://([^/]+)/?', url).group(1)
                    domain_id = get_domain_id(cursor, domain)
                    if not domain_id:
                        domain_id = insert_domain(cursor, domain)
                        if debug:
                            print(f"New domain discovered: {domain}")

                    update_url_depth(cursor, url, current_depth + 1)
                    conn.commit()

                    for link in links:
                        link_domain = re.match(r'http[s]?://([^/]+)/?', link).group(1)
                        link_domain_id = get_domain_id(cursor, link_domain)
                        if not link_domain_id:
                            link_domain_id = insert_domain(cursor, link_domain)
                            if debug:
                                print(f"New domain discovered: {link_domain}")

                        if link not in crawled:
                            insert_url(cursor, link_domain_id, link, 1)  # Set depth to 1 for new URLs
                            conn.commit()

                            if debug:
                                print(f"New URL discovered: {link}")

                        new_to_crawl.add((link, 1))  # New URLs to be crawled start at depth 1

                    crawled.add(url)
                    time.sleep(0.04)

            to_crawl = new_to_crawl

        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)


if __name__ == "__main__":
    debug = False  # Set this to True to enable debug output

    db_config = {
        'user': getenv("MARIADB_USERNAME"),
        'password': getenv("MARIADB_PASSWORD"),
        'host': getenv("MARIADB_HOST"),
        'database': 'cyberminer',
        'raise_on_warnings': True,
    }

    crawl(db_config, debug)
