--problem: find programmer which solve all problem with larger than or equal to 30 minutes order by name. each submission have to smaller and or equal to 10 minutes
with qualified_user as (
    -- find qualied user with user_id (filter, aggregate, and filter base on aggregate result), (where, group by, having)
    select
    user_id
    from submissions
    where datediff(minute, start_time, submission_time) <= 10
    group by user_id
    having sum(datediff(minutes, start_time, submission_time)) >= 30
)
--get user name given user_id (filter using join)
select us.name
from users as us
right join qualified_user as qu on us.id = qu.user_id

--or
select
us.name
from users as us
left join submissions as su on us.id = su.user_id
where su.datediff(minute, start_time, submission_time) <= 10
group by su.user_id, us.name
having sum(datediff(minute, start_time, submission_time)) >= 30
