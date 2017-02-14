SET search_path TO ate;

CREATE TABLE badrowcount AS
  SELECT table1.text, table2.number
  FROM table1 JOIN table2 ON table1.id = table2.foreign_id
  UNION ALL
  SELECT CAST('zzzz' AS varchar(50)) AS text, CAST(9.99 AS double precision) AS number;
