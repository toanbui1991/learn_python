--problem: assign student grad base on their mark. Or problem of lable base on range of value.
--learning: 
  --learning one: range join to assign label base on range of value
  --learning two: order by multiple criteria
select if(gr.grade >= 8, st.name, NULL) as name
, gr.grade
, st.marks
from students as st
left join grades as gr on st.marks >= gr.min_mark and st.marks <= gr.max_mark
order by gr.grade desc, st.name asc, st.marks asc
