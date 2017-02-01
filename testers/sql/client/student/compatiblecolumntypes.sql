SET search_path TO ate;

SELECT table1.text::text, table2.number::real
FROM table1 JOIN table2 ON table1.id = table2.foreign_id
ORDER BY text;
