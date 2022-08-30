with lead_ctx as (
    select company_code, 
    count(lead_manager_code) as lead_count
    from lead_manager  
    group by company_code
),
senior_ctx as (
    select company_code,
    count(senior_manager_code) as senior_count
    from senior_manager
    group by company_code
),
manager_ctx as (
    select company_code,
    count(manager_code) as manager_count
    from manager
    group by company_code
),
employee_ctx as (
    select company_code,
    count(employee_code) as employee_count
    from employee
    group by employee_code
)
select co.company_code, co.founder, le.lead_count, se.senior_count, ma.manager_count, em.employee_count
from company as co
left join lead_ctx as le on co.company_code = le.company_code
left join senior_ctx as se on co.company_code = se.company_code
left join manager_ctx as ma on co.company_code = ma.company_code
left join employee_ctx as em on co.company_code = em.company_code
