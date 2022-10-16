/*
problem: 
*/
--chose the number on player in group
SELECT group_id, player_id,
RANK() OVER (partiton by group_id ORDER BY score DESC, player_id) rnk
FROM
    --compute score of each player in each group
    (SELECT p.group_id group_id, t.player_id player_id, SUM(score) score
    FROM
    --reconstruct matches table from wide to long
        (SELECT first_player player,
        first_score score, match_id
        FROM matches
        UNION
        SELECT second_player player,
        second_score score, match_id
        FROM matches) t
    LEFT JOIN players p ON p.player_id = t.player
    GROUP BY p.group_id, t.player_id) s
WHERE rnk = 1
ORDER BY group_id
/*
my solution:
    one: find score of each player (change matches from wide to long to compute total score of each player)
    two: rank player score in each group 
        (left join between player_score with players to get group,
        rank() over(parition by group order by score desc, player_id)
        choose first player from rank
        )
*/
