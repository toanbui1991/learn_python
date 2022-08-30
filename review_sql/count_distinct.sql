select co.company_code, co.founder
, count(distinct le.lead_manager_code)
, count(distinct se.senior_manager_code)
, count(distinct ma.manager_code)
, count(distinct em.employee_code)
from company as co
left join lead_manager as le on co.company_code = le.company_code
left join senior_manager as se on le.lead_manager_code = se.lead_manager_code
left join manager as ma on se.senior_manager_code = ma.senior_manager_code
left join employee as em on ma.manager_code = em.manager_code
group by co.company_code, co.founder