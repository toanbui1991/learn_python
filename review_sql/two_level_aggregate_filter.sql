-- find the score for each challenge_id, group by level 1
-- find total score for each hacker_id, group by level 2
-- order by score desc, order by hacker_id asc
-- eclude hacker with total score is 0, can not use aggregrate in where clause

--learning:
  --one: using commont table expression to do the aggregate
  --two: filter and ordering base on that ctx
with score_ctx as (
    select hacker_id
    , challenge_id
    , max(score) as max_score
    from submissions
    group by hacker_id, challenge_id
),
total_score_ctx as (
    select hacker_id
    , sum(max_score) as total_score
    from score_ctx
    group by hacker_id
)
select ha.hacker_id
, ha.name
, ts.total_score
from hackers as ha
left join total_score_ctx as ts on ha.hacker_id = ts.hacker_id
where ts.total_score > 0
order by ts.total_score desc, ha.hacker_id asc