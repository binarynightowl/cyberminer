use cyberminer;

INSERT INTO domains (domain_name)
VALUES ('example.com'),
       ('utdallas.edu'),
       ('google.com');

INSERT INTO urls (domain_id, path, depth)
VALUES (1, 'https://example.com', 1),
       (2, 'https://utdallas.edu', 1),
       (3, 'https://google.com', 1);