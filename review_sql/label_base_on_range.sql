--problem: label item base on it's property and range criteria
--problem: label student grade base on marks range
-- label grade for student given mark
-- name student >= 8, order by grade desc, name
-- name student < 8 is NULL, order by mark asc

with student_grade as (
    select
    st.name
    , st.marks
    , gr.grade
    from students as st
    left join grades as gr on st.marks >= gr.min_mark and st.marks <= gr.max_mark
)
select
iif(grade >= 8, name, NULL) as name
,grade
,marks
from student_grade
order by grade desc, name, marks asc