SET search_path TO ate;

CREATE TABLE badcolumntypes AS
  SELECT table1.id AS word, table2.number
  FROM table1 JOIN table2 ON table1.id = table2.foreign_id;
