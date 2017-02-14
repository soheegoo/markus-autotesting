SET search_path TO ate;

CREATE TABLE compatiblecolumntypes AS
  SELECT CAST(table1.text AS text) AS text, CAST(table2.number AS real) AS number
  FROM table1 JOIN table2 ON table1.id = table2.foreign_id;
