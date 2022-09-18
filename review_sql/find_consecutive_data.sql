--problem: in a consecutive data table find data point which is not consecutive
--problem: start_date and end date different is one and project will have all task in consecutive
-- solution:
    --find row which is start of project and find row which is end of project
    --join with condition of start_index = end_index to find project.
-- learn:
  --one: using datediff(datepart, start_date, end_date)
-- find star row of consecutive rows
with t1  as (select start_date,
         row_number()over(order by start_Date) as s_rn
        from projects
        where start_date not in (select end_date from projects)
        ),
-- find end row of consecutive rows
 t2 as(select end_date
        ,row_number()over(order by end_Date) as ss_rn
        from projects
        where end_date not in (select start_date from projects)
       )
-- conbine two result
select start_date,end_date
from t1,t2
where t1.s_rn = t2.ss_rn
order by
datediff(day,start_date,End_date),start_date
;

-- the other solution is to using left join instead of cross join because we know project index
with t1  as (select start_date,
         row_number()over(order by start_Date) as s_rn
from projects
where start_date not in (select end_date from projects)
        ),

 t2 as(select end_date
        ,row_number()over(order by end_Date) as ss_rn
from projects
where end_date not in (select start_date from projects)
       )


select t1.start_date,t2.end_date
from t1
left join t2 on t1.s_rn = t2.ss_rn
order by
datediff(day,t1.start_date,t2.end_date), t1.start_date
; 