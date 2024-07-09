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