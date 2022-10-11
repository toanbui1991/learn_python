/*
find all combination of all customer and product
sybtax of cartesian product
*/
SELECT C.CustomerID, C.CustFirstName, C.CustLastName,
  P.ProductNumber, P.ProductName, P.ProductDescription
FROM Customers AS C, Products AS P;

/*
list all product which have been sold
*/
SELECT O.OrderNumber, O.CustomerID, OD.ProductNumber 
FROM Orders AS O 
INNER JOIN Order_Details AS OD
ON O.OrderNumber = OD.OrderNumber;

-- Listing 8.3 Listing all customers and all products, flagging products already purchased by each customer
-- step one: find all combination between customer and product
-- step two: aggregate to find who by what and how many
-- step three: left join between one and two and use case  when testing then result one for condition.
SELECT CustProd.CustomerID, CustProd.CustFirstName, CustProd.CustLastName,
  CustProd.ProductNumber, CustProd.ProductName, 
  (CASE WHEN OrdDet.OrderCount > 0 
    THEN 'You purchased this!'
    ELSE ' ' 
  END) AS ProductOrdered
FROM
(SELECT C.CustomerID, C.CustFirstName, C.CustLastName,
  P.ProductNumber, P.ProductName, P.ProductDescription
FROM Customers AS C, Products AS P) AS CustProd
LEFT JOIN
(SELECT O.CustomerID, OD.ProductNumber, Count(*) AS OrderCount
FROM Orders AS O INNER JOIN Order_Details AS OD
  ON O.OrderNumber = OD.OrderNumber
GROUP BY O.CustomerID, OD.ProductNumber) AS OrdDet
  ON CustProd.CustomerID = OrdDet.CustomerID
  AND CustProd.ProductNumber = OrdDet.ProductNumber
ORDER BY CustProd.CustomerID, CustProd.ProductName;

-- the second approach to solve above problem. I like the first approach more
SELECT C.CustomerID, C.CustFirstName, C.CustLastName,
  P.ProductNumber, P.ProductName,
  (CASE WHEN C.CustomerID IN
    (SELECT Orders.CustomerID
     FROM Orders INNER JOIN Order_Details
       ON Orders.OrderNumber = Order_Details.OrderNumber
     WHERE Order_Details.ProductNumber = P.ProductNumber)
     THEN 'You purchased this!'
     ELSE ' ' 
  END) AS ProductOrdered
FROM Customers AS C, Products AS P
ORDER BY C.CustomerID, P.ProductName;