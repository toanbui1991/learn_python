--item 24: using syntax case when then do .. else do end.
--item 25: find customer who order skateboard and alose order helmet, knee pads and gloves.
  --solution: find four subquery with distinct customer id given each product name. inner join to find customer id.
  --solution: using where exists .. and exist to test customer who have bouth a list of product

--item 26: data combination,
  --problem one: find combination of customer and product from table customer, order, order_detail and product
  -- solution: we left join and then select disctinct to find combination of customer and product (avoid customer by sample product multiple time)
  --problem two: from products table from product of interest.
  -- solution: use where and in test
  --problem three: given we have customer_product_combination, product_of_interest find customer who interest or purchase all project in product of interes
  --solution: find customer_product_combination, find product_of_interes. 
  --reference: https://stackoverflow.com/questions/68694240/find-the-names-of-the-suppliers-who-supply-all-the-parts-in-ms-access

--item 27: Know how to correctly filter range of date in a column.
    -- analyze: we have to know the data type of column (date, or datetime)
    -- solution: use <= and < instead of between and. and have to know date function like date, convert or cast
    -- and data type like date and datetime.

--item 29: correctly filter right side of a left join.
    --analyze: we do left join between customer and order and filter with where date range that order happend.
    --because of sql execution sequence from (include join) > where. Therefore filter will cause missing customer if customer do not have any order
    --solution: filter order in subquery first, and then join between customer and filtered orders
    --example problem: total order value of each customer in a period of name.
    --solution: use common table expression to compute aggregate table -> join between customer with aggregated data -> use isnull to handle customer which do not have any order

SELECT CP.CustomerID, CP.CustFirstName, CP.CustLastName
FROM CustomerProducts AS CP
CROSS JOIN ProdsOfInterest AS PofI
WHERE CP.ProductName = PofI.ProductName
GROUP BY CP.CustomerID, CP.CustFIrstName, CP.CustLastName
HAVING COUNT(CP.ProductName) =
(SELECT COUNT(ProductName) FROM ProdsOfInterest);