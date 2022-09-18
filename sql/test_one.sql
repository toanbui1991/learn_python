--find duplicate email given table
with duplicate_data as (
    select id
    , now_number(partition by email order by id) as duplicate_test 
    from customer_table
),
unique_data as (
    select id
    from duplicate_data
    where duplicate_test = 1
)

delete customer_table
where id in not (
    select id
    from unique_data
)