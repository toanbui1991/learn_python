/*
problem: find customer who have bougt all product in product of interest
solution:
    one: find unique or distinct combination of customer and product they have bougt
    two: find a set of product of interest
    three: join one and two base on product key. group customer to count number of product and compare of number of product in the interesting set.
analyze:  join with product key will  increase the number of row in the result table, but in the left side (customer side) customer do not bought product will return null.
    Therefore, group by and then count will return the number of product which have been bought by that customer.
    Compare the result (number of product which have been bought) to the number of product in the set of interest which will return customer who have bought all product in set of product
*/

CREATE VIEW CustomerProducts AS --combination of customer and product
SELECT DISTINCT Customers.CustomerID, Customers.CustFirstName, 
  Customers.CustLastName, Products.ProductName
FROM Customers INNER JOIN Orders
  ON Customers.CustomerID = Orders.CustomerID
INNER JOIN Order_Details
  ON Orders.OrderNumber = Order_Details.OrderNumber
INNER JOIN Products
  ON Products.ProductNumber = Order_Details.ProductNumber;
GO

CREATE VIEW ProdsOfInterest AS -- product off interest
SELECT Products.ProductName
FROM Products
WHERE ProductName IN 
  ('Skateboard', 'Helmet', 'Knee Pads', 'Gloves');
GO

--we use cross join and then where I think it is the same with inner join with on key
SELECT CP.CustomerID, CP.CustFirstName, CP.CustLastName
FROM CustomerProducts AS CP 
CROSS JOIN ProdsOfInterest AS PofI
WHERE CP.ProductName = PofI.ProductName
GROUP BY CP.CustomerID, CP.CustFIrstName, CP.CustLastName
HAVING COUNT(CP.ProductName) = 
  (SELECT COUNT(ProductName) FROM ProdsOfInterest);