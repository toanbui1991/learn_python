--problem 20: count total product in category. solution: group by with count(*)
--problem 21: totoal customer per country, city. Solution: group by country, city with sum
--problem 22: products that need reordering: filter with where
--problem 23: products that need reordering: filter with where stock <= reorder_level, discontinued = 0
--problem 24: customer list by region: order by region and customer_id
--problem 25: high freight charged: compute aggregate and then order by that aggregate value
--problem 26: high freight charges in 2015: where will filter first, and then aggregate function with group by. having filter after aggreate
--problem 28: hight freight charges with between. 
--be careful between with datetime and date format in where clause. because the auto convert of string to date and datetime format 
--problem 29: hight freight last year. where with dateadd(date part, int, data column). other datetime function is datediff()
--proble 30: inventory list. simmple joint
--problem 31: customer with no order. join between customers and order, filter with where when order_id is null