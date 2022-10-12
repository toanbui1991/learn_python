
/*
problem: find customer who have order not only Skateboard but also Helmet, Knee Pads, and Gloves with the and condition
*/

--this is wrong because this is or condition
SELECT C.CustomerID, C.CustFirstName, C.CustLastName
FROM Customers AS C
WHERE C.CustomerID IN 
  (SELECT CustomerID FROM Orders
  INNER JOIN Order_Details
  ON Orders.OrderNumber = Order_Details.OrderNumber
  INNER JOIN Products
  ON Products.ProductNumber = Order_Details.ProductNumber
  WHERE Products.ProductName 
    IN ('Skateboard', 'Helmet', 'Knee Pads', 'Gloves'));


--this is correct approach for and condition with inner join
SELECT C.CustomerID, C.CustFirstName, C.CustLastName
FROM Customers AS C INNER JOIN
  (SELECT DISTINCT Orders.CustomerID
  FROM Orders INNER JOIN Order_Details
  ON Orders.OrderNumber = Order_Details.OrderNumber
  INNER JOIN Products 
  ON Products.ProductNumber = Order_Details.ProductNumber
  WHERE Products.ProductName = 'Skateboard') AS OSk
ON C.CustomerID = OSk.CustomerID
INNER JOIN
  (SELECT DISTINCT Orders.CustomerID
  FROM Orders INNER JOIN Order_Details
  ON Orders.OrderNumber = Order_Details.OrderNumber
  INNER JOIN Products 
  ON Products.ProductNumber = Order_Details.ProductNumber
  WHERE Products.ProductName = 'Helmet') AS OHel
ON C.CustomerID = OHel.CustomerID
INNER JOIN
  (SELECT DISTINCT Orders.CustomerID
  FROM Orders INNER JOIN Order_Details
  ON Orders.OrderNumber = Order_Details.OrderNumber
  INNER JOIN Products 
  ON Products.ProductNumber = Order_Details.ProductNumber
  WHERE Products.ProductName = 'Knee Pads') AS OKn
ON C.CustomerID = OKn.CustomerID
INNER JOIN
  (SELECT DISTINCT Orders.CustomerID
  FROM Orders INNER JOIN Order_Details
  ON Orders.OrderNumber = Order_Details.OrderNumber
  INNER JOIN Products 
  ON Products.ProductNumber = Order_Details.ProductNumber
  WHERE Products.ProductName = 'Gloves') AS OGl
ON C.CustomerID = OGl.CustomerID;

--this approach we use function with and condition in where
CREATE FUNCTION CustProd(@ProdName VarChar(50)) RETURNS Table
AS 
RETURN (SELECT Orders.CustomerID AS CustID
FROM Orders INNER JOIN Order_Details
ON Orders.OrderNumber = Order_Details.OrderNumber
INNER JOIN Products
ON Products.ProductNumber = Order_Details.ProductNumber
WHERE ProductName = @ProdName);
GO

SELECT C.CustomerID, C.CustFirstName, C.CustLastName
FROM Customers AS C 
WHERE C.CustomerID IN
  (SELECT CustID FROM CustProd('Skateboard'))
AND C.CustomerID IN
  (SELECT CustID FROM CustProd('Helmet'))
AND C.CustomerID IN
  (SELECT CustID FROM CustProd('Knee Pads'))
AND C.CustomerID IN
  (SELECT CustID FROM CustProd('Gloves'));

-- the same idea with and condition using exist keyword
SELECT C.CustomerID, C.CustFirstName, C.CustLastName
FROM Customers AS C 
WHERE EXISTS
  (SELECT Orders.CustomerID
  FROM Orders INNER JOIN Order_Details
  ON Orders.OrderNumber = Order_Details.OrderNumber
  INNER JOIN Products 
  ON Products.ProductNumber = Order_Details.ProductNumber
  WHERE Products.ProductName = 'Skateboard'
  AND Orders.CustomerID = C.CustomerID)
AND EXISTS
  (SELECT Orders.CustomerID
  FROM Orders INNER JOIN Order_Details
  ON Orders.OrderNumber = Order_Details.OrderNumber
  INNER JOIN Products 
  ON Products.ProductNumber = Order_Details.ProductNumber
  WHERE Products.ProductName = 'Helmet'
  AND Orders.CustomerID = C.CustomerID)
AND EXISTS
  (SELECT Orders.CustomerID
  FROM Orders INNER JOIN Order_Details
  ON Orders.OrderNumber = Order_Details.OrderNumber
  INNER JOIN Products 
  ON Products.ProductNumber = Order_Details.ProductNumber
  WHERE Products.ProductName = 'Knee Pads'
  AND Orders.CustomerID = C.CustomerID)
AND EXISTS
  (SELECT Orders.CustomerID
  FROM Orders INNER JOIN Order_Details
  ON Orders.OrderNumber = Order_Details.OrderNumber
  INNER JOIN Products 
  ON Products.ProductNumber = Order_Details.ProductNumber
  WHERE Products.ProductName = 'Gloves'
  AND Orders.CustomerID = C.CustomerID);


  /*
  problem: find customer who by skateboard but not protected produdct (not one of a set of product)
  */
  SELECT C.CustomerID, C.CustFirstName, C.CustLastName
FROM Customers AS C 
WHERE C.CustomerID IN
  (SELECT Orders.CustomerID
  FROM Orders INNER JOIN Order_Details
  ON Orders.OrderNumber = Order_Details.OrderNumber
  INNER JOIN Products 
  ON Products.ProductNumber = Order_Details.ProductNumber
  WHERE Products.ProductName = 'Skateboard')
AND C.CustomerID NOT IN
  (SELECT Orders.CustomerID
  FROM Orders INNER JOIN Order_Details
  ON Orders.OrderNumber = Order_Details.OrderNumber
  INNER JOIN Products 
  ON Products.ProductNumber = Order_Details.ProductNumber
  WHERE Products.ProductName 
    IN ('Helmet', 'Gloves', 'Knee Pads'));

-- the second approach with or condition in set of in test
CREATE FUNCTION CustProd(@ProdName VarChar(50)) RETURNS Table
AS 
RETURN (SELECT Orders.CustomerID AS CustID
FROM Orders INNER JOIN Order_Details
ON Orders.OrderNumber = Order_Details.OrderNumber
INNER JOIN Products
ON Products.ProductNumber = Order_Details.ProductNumber
WHERE ProductName = @ProdName);
GO

SELECT C.CustomerID, C.CustFirstName, C.CustLastName
FROM Customers AS C 
WHERE C.CustomerID IN
  (SELECT CustID FROM CustProd('Skateboard'))
AND (C.CustomerID NOT IN 
  (SELECT CustID FROM CustProd('Helmet'))
OR C.CustomerID NOT IN
  (SELECT CustID FROM CustProd('Gloves'))
OR C.CustomerID NOT IN
  (SELECT CustID FROM CustProd('Knee Pads')));
GO