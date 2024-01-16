CREATE TABLE COMPLEX_NETWORK_GRAPHS
(
    id         SERIAL PRIMARY KEY,
    timestamp  TIMESTAMP DEFAULT NOW(),
    graph_json TEXT NOT NULL
);

CREATE TABLE TRENDS
(
    id         SERIAL PRIMARY KEY,
    timestamp  TIMESTAMP DEFAULT NOW(),
    ticker     TEXT NOT NULL,
    trend      TEXT NOT NULL,
    price      NUMERIC(10,2) NOT NULL
);

CREATE TABLE STOCK_EXCHANGES
(
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    timestamp   TIMESTAMP,
    ticker      TEXT NOT NULL,
    price       NUMERIC(10, 2) NOT NULL,
    currency    TEXT NOT NULL,
    amount      INTEGER NOT NULL,
    seller_id   UUID NOT NULL,
    buyer_id    UUID NOT NULL
);

CREATE TABLE TRADERS
(
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    document    TEXT NOT NULL,
    email       TEXT NOT NULL
);

INSERT INTO TRADERS (id, first_name, last_name, document, email) VALUES
    ('201264f3-3148-4d2d-a1f5-fdb01f4eeaad', 'Catherine', 'Franecki', '830-07-1389', 'catherine_franecki@yahoo.com'),
    ('7ac0dbbe-f296-47f3-85f6-345891197df6', 'Alta', 'Hilpert', '859-98-2293', 'alta5@hotmail.com'),
    ('73c84595-33a1-4683-8a9a-6418f5c0ba2a', 'Yasmin', 'Rutherford', '500-65-7945', 'yasmin.rutherford@yahoo.com'),
    ('c0389a82-8533-4808-a502-d767c79d19d8', 'Leland', 'Altenwerth', '783-81-3647', 'leland.altenwerth45@gmail.com'),
    ('041a002d-a9e1-453d-b7c9-e0ded4c0a110', 'Genoveva', 'Gislason', '226-89-1780', 'genoveva71@yahoo.com'),
    ('d5ef226e-3b6f-4485-b37e-31d9949bcb8e', 'Braulio', 'Hettinger', '768-03-4053', 'braulio_hettinger79@hotmail.com'),
    ('377a1452-ba4c-41f7-a930-20a01bcdf5b0', 'Jessyca', 'Steuber', '826-97-7291', 'jessyca.steuber@hotmail.com'),
    ('e14767d9-8d37-43c7-9731-036ce7af04ab', 'Nella', 'Greenholt', '657-35-0849', 'nella59@hotmail.com'),
    ('d94ce689-a03a-48c3-acd7-ca2076e01d8e', 'Amanda', 'Russel', '231-30-3765', 'amanda38@gmail.com'),
    ('fc8fa848-3673-4ae9-a078-42ae267107bc', 'Wilburn', 'Daniel', '080-16-0337', 'wilburn58@gmail.com')
;