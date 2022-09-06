--problem 32: high value customer who have at least one order larger than 10000 usd.
-- learning: the sql execution order: from (include select), where, group by, having, select, order by, limit
--problem 33: high value customer who have total orders in a year > 15000 usd.
-- the different between problem 32 vs problem 33 is the definition of high value customer. therefore different way to group by.
-- problem 32 add one more level order_id.
-- problem 34: high value customer with discount. in this problem we consider discount price in condition to decide high value custom
-- therefore: having sum(quantity * unit_price(1-discount))
-- problem 35: find orders which happen at the end of month. sql server use function eomonth(date), mysql use last_day(date)
-- problem 36: find order with multiple line item.
-- problem 37: select random data point. using order by newid() in sql server or order by uuid() in mysql
-- problem 38: find accidential order double entry using group by order_id, quantity, and having count(*) > 1. quantity is the second attribute use to detect duplicate.
-- problem 39: get more detail about order given we have fine possible douplicate order. find possible duplicate order using common table expression 
-- problem 40: the same as 39 but use join and sub query to filter.
-- problem 41 - 47: late order vs total order group by employee_id.
    -- one: using common table expression to find number of late order by employee_id and number of total order
    -- two: fix null problem cause by left join but missing key from the right side with isnull to test(test_value, otherwise_value)
    -- three: fix percentage decimal with convert(decimal(10,2), number) sql server or cat(number as decial(10,2))
-- problem 48-51: label customer by total amount of order. using case when then for label or using join with between condition for a fexible labeling.
-- problem 56-57: find customer which have multiple order in period of 5 days.

--problem 57: using lead window function.
With NextOrderDate as (
    Select CustomerID
    ,OrderDate = convert(date, OrderDate)
    ,NextOrderDate = convert(
    date ,Lead(OrderDate,1) OVER (Partition by CustomerID order by
    CustomerID, OrderDate) )
    From Orders 
    )
Select CustomerID
,OrderDate 
,NextOrderDate 
,DaysBetweenOrders = DateDiff (dd, OrderDate,
NextOrderDate) 
From NextOrderDate 
Where DateDiff (dd, OrderDate,
NextOrderDate) <= 5