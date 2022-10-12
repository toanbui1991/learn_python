/*
problem: filter right side of the left join can cause missing data
*/
SELECT Customers.CustomerID, Customers.CustFirstName, 
  Customers.CustLastName, Orders.OrderNumber, Orders.OrderDate,
  Orders.OrderTotal
FROM Customers LEFT JOIN Orders
  ON Customers.CustomerID = Orders.CustomerID
WHERE Orders.OrderDate BETWEEN CAST('2015-10-01' AS DATETIME)
  AND CAST('2015-12-31' AS DATETIME);

/*
problem: filter the right side of a left join without cause missing data
*/
--the first approach is to add or is null condition
SELECT Customers.CustomerID, Customers.CustFirstName, 
Customers.CustLastName, Orders.OrderNumber, Orders.OrderDate,
Orders.OrderTotal
FROM Customers LEFT JOIN Orders
  ON Customers.CustomerID = Orders.CustomerID
WHERE (Orders.OrderDate BETWEEN CAST('2015-10-01' AS DATETIME)
    AND CAST('2015-12-31' AS DATETIME))
  OR Orders.OrderNumber IS NULL;

--the second approach is filter the right side just and then join later
SELECT Customers.CustomerID, Customers.CustFirstName, 
  Customers.CustLastName, OFiltered.OrderNumber, 
  OFiltered.OrderDate, OFiltered.OrderTotal
FROM Customers LEFT JOIN 
  (SELECT Orders.OrderNumber, Orders.CustomerID, 
    Orders.OrderDate, Orders.OrderTotal
  FROM Orders
  WHERE Orders.OrderDate BETWEEN CAST('2015-10-01' AS DATE)
    AND CAST('2015-12-31' AS DATE)) AS OFiltered
  ON Customers.CustomerID = OFiltered.CustomerID;