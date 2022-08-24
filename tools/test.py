
from bpagrab.sandbox import *



query = """with logs as (
select 
	payment_to_booking_id
	, created 
from grab_money.payment_to_booking_log
where comments = 'Complete a booking. Auto-approval not applicable'
	and year||'-'||month||'-'||day  >=  CAST(CURRENT_DATE - INTERVAL '7' DAY AS VARCHAR)
) 
, reviewed as ( 
select distinct 
	bk.id
	, bk.status
	, case when status = 4 then 'rejected'
		when status = 8 then 'approved'
		when status = 11 then 'resolved' 
		else 'unknown' end as status_desc
	, bk.booking_code
	, bk.currency
	, bk.total
	, bk.tolls_and_others
	, bk.promo_value
	, bk.created
	, bk.updated
from grab_money.payment_to_booking bk
where bk.year||'-'||bk.month||'-'||bk.day  >=  CAST(CURRENT_DATE - INTERVAL '1' DAY AS VARCHAR)
	and bk.id in (select payment_to_booking_id from logs)
)
select *
from reviewed
limit 20000"""

df=presto.extract(query)
