-- problem: aggregate and then filter with window function (number of element in group, compare element with max of element)
-- group by number of challenge
-- problem: commpute number of challenges created by students (aggregate), and each group of number of challenge choose one student
-- except group which archive max number of challenge
-- each group of number of challenge choose one, except group which have max number of challenge.

-- learning: the syntax of window functions
--step one: find nchalleges of each hacker
with num_challenges as (
    select 
    hacker_id
    , count(1) as nchallenges
    from challenges
    group by hacker_id
),
--step two: find filter condition, each nchallenges group take 1, except max group
challenges_condition as (
    select hacker_id
    , nchallenges
    , count(1) over(partition by nchallenges) as group_challenges
    , max(nchallenges) over() as max_challenges
    from num_challenges
)
--get name, filter and order
select
ha.hacker_id
, ha.name
, ch.nchallenges
from hackers as ha
left join challenges_condition as ch on ha.hacker_id = ch.hacker_id
where ch.group_challenges = 1
or ch.nchallenges = max_challenges
order by ch.nchallenges desc, ha.hacker_id