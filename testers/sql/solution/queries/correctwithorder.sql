CREATE TABLE oracle_correctwithorder AS
  SELECT table1.text, table2.number
  FROM table1 JOIN table2 ON table1.id = table2.foreign_id;
