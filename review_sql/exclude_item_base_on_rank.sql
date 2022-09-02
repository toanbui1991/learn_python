-- group by number of challenge
-- each group of number of challenge choose one, except group which have max number of challenge.

-- learning:
  --one: using count(1) to count number of row
  --two: using count(1) over(parition by nchalleges) and max(nchalleges) over() with window function syntax
WITH c AS(
    SELECT hacker_id, Count(1) nchallenges
      FROM Challenges
    GROUP BY hacker_id
), mc AS (
    SELECT *, Count(1) OVER(PARTITION BY nchallenges) xrpt, Max(nchallenges) OVER() mch
     FROM c
)
SELECT h.hacker_id, h.name, mc.nchallenges
  FROM mc
  JOIN Hackers h ON h.hacker_id = mc.hacker_id
 WHERE mc.xrpt = 1
    OR mc.nchallenges = mch
ORDER BY mc.nchallenges DESC, h.hacker_id;