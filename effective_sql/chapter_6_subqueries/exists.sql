/*
reading section about exists keyword sql
exists: is logical operation allow us to check data point exist or not, if exist return True if subquery return 1 or more row
exists will check every row if the subquery return or not
*/


/*
analyze:
    below will return every rows from customers table because select null will return on row null
*/
SELECT
    customer_id,
    first_name,
    last_name
FROM
    sales.customers
WHERE
    EXISTS (SELECT NULL)
ORDER BY
    first_name,
    last_name;


/*
problem: find customer which have more than two orders using exist
*/
SELECT
    customer_id,
    first_name,
    last_name
FROM
    sales.customers c
WHERE
    EXISTS (
        SELECT
            COUNT (*)
        FROM
            sales.orders o
        WHERE
            customer_id = c.customer_id
        GROUP BY
            customer_id
        HAVING
            COUNT (*) > 2
    )
ORDER BY
    first_name,
    last_name;



/*
problem: find order of customer who live in San Jose city
*/
--the first approach using in
SELECT
    *
FROM
    sales.orders
WHERE
    customer_id IN (
        SELECT
            customer_id
        FROM
            sales.customers
        WHERE
            city = 'San Jose'
    )
ORDER BY
    customer_id,
    order_date;

-- the second approach use exists
SELECT
    *
FROM
    sales.orders o
WHERE
    EXISTS (
        SELECT
            customer_id
        FROM
            sales.customers c
        WHERE
            o.customer_id = c.customer_id
        AND city = 'San Jose'
    )
ORDER BY
    o.customer_id,
    order_date;