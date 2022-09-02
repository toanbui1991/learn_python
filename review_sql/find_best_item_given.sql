-- find the best wands, minimum number of gold with combination of power and age and it's have to be not evil

-- find wands that is not evil 
with not_evil as (
    select 
    wa.id
    , wp.age
    , wa.coins_needed
    , wa.power
    from wands as wa
    left join wands_property as wp on wa.code = wp.code
    where wp.is_evil = 0
)
-- find wand which min of coin given power and age
select * 
from not_evil as ne1
where coins_needed = (
    select min(coins_needed)
    from not_evil as ne2
    where ne1.power = ne2.power and ne1.age = ne2.age
)
order by ne1.power desc, ne1.age desc