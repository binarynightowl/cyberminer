CREATE DATABASE cyberminer;

USE cyberminer;

CREATE TABLE domains
(
    id          INT AUTO_INCREMENT PRIMARY KEY,
    domain_name TEXT NOT NULL
);

CREATE TABLE urls
(
    id        INT AUTO_INCREMENT PRIMARY KEY,
    domain_id INT  NOT NULL,
    path      TEXT NOT NULL UNIQUE,
    depth     INT DEFAULT 1,
    FOREIGN KEY (domain_id) REFERENCES domains (id)
);

CREATE TABLE words
(
    id   INT AUTO_INCREMENT PRIMARY KEY,
    word TEXT NOT NULL
);

CREATE TABLE word_count
(
    id      INT AUTO_INCREMENT PRIMARY KEY,
    count   INT NOT NULL,
    word_id INT NOT NULL,
    url_id  INT NOT NULL,
    FOREIGN KEY (word_id) REFERENCES words (id),
    FOREIGN KEY (url_id) REFERENCES urls (id)
);

ALTER TABLE words
    CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

ALTER TABLE word_count
    CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

CREATE TABLE ignored_domains
(
    id     INT AUTO_INCREMENT PRIMARY KEY,
    domain INT NOT NULL,
    FOREIGN KEY (domain) REFERENCES domains (id)
);

CREATE INDEX idx_urls_domain_id ON urls (domain_id);

CREATE INDEX idx_words_word ON words (word(255));

CREATE INDEX idx_word_count_word_id_url_id ON word_count (word_id, url_id);

CREATE UNIQUE INDEX idx_domains_domain_name ON domains (domain_name(255));

CREATE INDEX idx_urls_path ON urls (path(255));

CREATE INDEX idx_word_count_count ON word_count (count);

CREATE INDEX idx_word_count_composite ON word_count (word_id, url_id, count);

ALTER TABLE words
    ADD FULLTEXT INDEX ft_words_word (word);