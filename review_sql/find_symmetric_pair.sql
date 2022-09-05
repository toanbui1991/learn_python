-- find symetric points
SELECT x, y FROM functions f
WHERE EXISTS(SELECT 1 FROM functions WHERE y = f.x AND x = f.y)
GROUP BY x, y
HAVING x < y OR count(*) > 1
ORDER BY x;