-- summary and then exclude filter base on window function confition

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