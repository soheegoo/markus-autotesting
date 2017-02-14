SET search_path TO ate;

CREATE TABLE badcolumnorder AS
  SELECT table2.number, table1.word
  FROM table1 JOIN table2 ON table1.id = table2.foreign_id;
