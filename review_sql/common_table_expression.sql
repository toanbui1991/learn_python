--problem: get shortest and longest city name 
--learning:
  --one: order by column_one desc, column_two asc
  --two: common table expression
  --three: union statement syntax

--mysql common table expression: reference below query for syntax

with order_one as (
    select city, length(city) from station
    order by length(city) asc, city asc
    limit 1
),
order_two as (
    select city, length(city) from station
    order by length(city) desc, city asc
    limit 1
)
select city, length(city) from order_one
union all
select city, length(city) from order_two