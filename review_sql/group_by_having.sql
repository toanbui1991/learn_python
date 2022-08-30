-- find hacker which have complete fullscore more than 1
-- learning:
    -- one: we can calculate number of fullscore submission with sum and if function
    -- two: using where, group, having and order in one statement
select su.hacker_id
, ha.name
from submissions as su
left join hackers as ha on su.hacker_id = ha.hacker_id
left join challenges as ch on su.challenge_id = ch.challenge_id
left join difficulty as di on ch.difficulty_level = di.difficulty_level
group by su.hacker_id, ha.name
having sum(if(di.score = su.score, 1, 0)) > 1
order by sum(if(di.score = su.score, 1, 0)) desc, su.hacker_id asc