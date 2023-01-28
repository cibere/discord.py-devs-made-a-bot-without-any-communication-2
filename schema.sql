-- NOTE: the script will attempt to create a database if no
-- 'database.db' file is found, so do not worry about this.
-- Only update with new table definitions when adding them.

CREATE TABLE wallets (
  user_id INT PRIMARY KEY,
  balance INT DEFAULT 0
); -- PLEASE! CLOSE ALL QUERIES

CREATE TABLE items (
  item_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  item_name TEXT    UNIQUE,
  price     INT     NOT NULL
);

CREATE TABLE inventory ( 
  user_id INTEGER NOT NULL,
  item_id INTEGER NOT NULL,
  amount  INTEGER NOT NULL,
  PRIMARY KEY (user_id, item_id),
  FOREIGN KEY (item_id) REFERENCES items(item_id)
    ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE lottery (
  lot_id INTEGER PRIMARY KEY AUTOINCREMENT,
  bal   INTEGER NOT NULL,
  -- entries as list of user_ids
  entries TEXT NULL,
  winner INTEGER NULL,
  start_time INTEGER NOT NULL,
  end_time INTEGER NOT NULL,
  FOREIGN KEY (winner) REFERENCES wallets(user_id)
    ON DELETE CASCADE ON UPDATE CASCADE
);

-- ITEMS -- Feel free to add more!
INSERT INTO items(item_name, price) VALUES ('Rubber Duck', 1000);
INSERT INTO items(item_name, price) VALUES ('Code Editor', 2300);
INSERT INTO items(item_name, price) VALUES ('Candy', 200);
INSERT INTO items(item_name, price) VALUES ('Trampoline', 15000);
INSERT INTO items(item_name, price) VALUES ('Emoji', 50);
INSERT INTO items(item_name, price) VALUES ('Computer', 100);
INSERT INTO items(item_name, price) VALUES ('Nuke', 999999999999999999);
INSERT INTO items(item_name, price) VALUES ('Personal Robot', 1000);
INSERT INTO items(item_name, price) VALUES ('Rock', 5);
INSERT INTO items(item_name, price) VALUES ('Air', 1);
INSERT INTO items(item_name, price) VALUES ('Nothing', 10);