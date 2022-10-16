/*
 https://code.dennyzhang.com/report-contiguous-dates
 First generate a list of dates
   succeeded 2019-01-01
   succeeded 2019-01-02
   ...
   failed 2019-01-04
   ...
 Add group id for contiguous ranges
 Notice: dates themselves are contiguous
solution:
    one: find rank. if prev = period_state than rank else rank+1
*/
select period_state, min(date) as start_date, max(date) as end_date
from (
    select period_state, date,
         @rank := case when @prev = period_state then @rank else @rank+1 end as rank,
         @prev := period_state as prev
    from (
        select 'failed' as period_state, fail_date as date
        from Failed
        where fail_date between '2019-01-01' and '2019-12-31'
        union
        select 'succeeded' as period_state, success_date as date
        from Succeeded
        where success_date between '2019-01-01' and '2019-12-31') as t, 
        (select @rank:=0, @prev:='') as rows
    order by date asc) as tt
group by rank
order by rank

/*
idea: the different between row_number base on date and row_number group by status and order by date is define the group which have consecutive date.
we can use it to group by
*/
Select min(status)  period_state,
 min(dates) start_date,
 max(dates) end_date
  from 
(
Select dates,
 status,
 (row_number() over (order by dates) - row_number() over (partition by status order by dates)) rn2
  from
    (

    Select fail_date as dates,'missing' as status  from failed
    union
    select success_date as dates, 'present' as status from succeeded
    order by dates
    ) tmp 
order by dates ) tmp1 

where dates >= '2019-01-01'
group by rn2;