-- problem: count number of item in multiple hierachy table
-- problem: count employee, manager, senior manager, lead manager. get company code and founder name

select
ca.company_code
, ca.founder
, count(distinct em.lead_manager_code)
, count(distinct em.senior_manager_code)
, count(distinct em.manager_code)
, count(distinct em.employee_code)
from company as ca
left join employee as em on ca.company_code = em.company_code
group by ca.company_code, ca.founder
order by ca.company_code asc
