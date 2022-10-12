/*
find vender who have average deliver longer than the general everage:
idea: using having to filter aggregate value compare to the general value with cte or subquery
note: 
    where vs having? where for row filter vs having for filter after aggregate
    normal function vs window function in where? ca use normal function but can not use window function in where
*/
SELECT V.VendName, AVG(DateDiff(d, P.OrderDate, 
    P.DeliveryDate)) AS DeliveryDays
FROM Vendors AS V 
  INNER JOIN PurchaseOrders AS P
     ON V.VendorID = P.VendorID
WHERE P.DeliveryDate IS NOT NULL
  AND P.OrderDate BETWEEN '2015-10-01' AND '2015-12-31'
GROUP BY V.VendName
HAVING AVG(DateDiff(d, P.OrderDate, P.DeliveryDate)) > 
  (SELECT AVG(DateDiff(d, P2.OrderDate, P2.DeliveryDate))
   FROM PurchaseOrders AS P2
   WHERE P2.DeliveryDate IS NOT NULL
      AND P2.OrderDate BETWEEN '2015-10-01' AND '2015-12-31');

/*
problem: find product which sale larger than average of category sale
solution:
    one: compute average total sale of category
    two: compute average of each product and filter with one
*/

WITH CatProdData AS (
	SELECT C.CategoryID, C.CategoryDescription, P.ProductName, OD.QuotedPrice, OD.QuantityOrdered
	FROM Products AS P 
	   INNER JOIN Order_Details AS OD 
	     ON P.ProductNumber=OD.ProductNumber
	   INNER JOIN Categories AS C
	     ON C.CategoryID = P.CategoryID
	   INNER JOIN Orders AS O
	     ON O.OrderNumber = OD.OrderNumber
	WHERE O.OrderDate BETWEEN '2015-10-01' AND '2015-12-31'
)
SELECT D.CategoryDescription, D.ProductName, 
  SUM(D.QuotedPrice * D.QuantityOrdered) AS TotalSales
FROM CatProdData AS D
GROUP BY D.CategoryID, D.CategoryDescription, D.ProductName
HAVING SUM(D.QuotedPrice * D.QuantityOrdered) > --compute one and filter 
  (SELECT AVG(SumCategory) --compute one
   FROM 
    (SELECT D2.CategoryID, 
      SUM(D2.QuotedPrice *D2.QuantityOrdered) 
        AS SumCategory 
     FROM CatProdData AS D2
     WHERE D2.CategoryID = D.CategoryID
     GROUP BY D2.CategoryID, D2.ProductName) AS S 
GROUP BY CategoryID)
ORDER BY CategoryDescription, ProductName;