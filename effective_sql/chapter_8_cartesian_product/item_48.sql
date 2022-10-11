SELECT OD.ProductNumber,
  SUM(OD.QuantityOrdered * OD.QuotedPrice) AS ProductSales
FROM Order_Details AS OD
WHERE OD.ProductNumber IN 
   (SELECT P.ProductNumber
    FROM Products AS P INNER JOIN Categories AS C
        ON P.CategoryID = C.CategoryID
    WHERE C.CategoryDescription = 'Accessories')
GROUP BY OD.ProductNumber;


/*
problem: assign quantitle category to product base on aggregate value (total sale of a product)
idea: compare rank of product to a fixed quantitle number
step one: compute aggregate value
step two: compute rank of product base on aggregate value
step three: from on compute number of product
step four: from two and three assign quantitle of product base on the idea
*/

WITH ProdSale AS --sumary by product
  (SELECT OD.ProductNumber,
       SUM(OD.QuantityOrdered * OD.QuotedPrice) AS ProductSales
     FROM Order_Details AS OD
     WHERE OD.ProductNumber IN 
       (SELECT P.ProductNumber
        FROM Products AS P INNER JOIN Categories AS C
          ON P.CategoryID = C.CategoryID
        WHERE C.CategoryDescription = 'Accessories')
     GROUP BY OD.ProductNumber),

RankedCategories AS --ranked product by aggregate value
  (SELECT Categories.CategoryDescription, Products.ProductName, 
          ProdSale.ProductSales, 
          RANK() OVER (
            ORDER BY ProdSale.ProductSales DESC
          ) AS RankInCategory
   FROM Categories INNER JOIN Products 
     ON Categories.CategoryID = Products.CategoryID
   INNER JOIN ProdSale
     ON ProdSale.ProductNumber = Products.ProductNumber),

ProdCount AS -- count number of project
  (SELECT COUNT(ProductNumber) AS NumProducts 
   FROM ProdSale) 
--assign product to qualtitle category base on aggregate value
SELECT P1.CategoryDescription, P1.ProductName, 
    P1.ProductSales, P1.RankInCategory, 
    (CASE WHEN RankInCategory <= ROUND(0.2 * NumProducts, 0)
            THEN 'First' 
          WHEN RankInCategory <= ROUND(0.4 * NumProducts,0)
            THEN 'Second' 
          WHEN RankInCategory <= ROUND(0.6 * NumProducts,0)
            THEN 'Third' 
          WHEN RankInCategory <= ROUND(0.8 * NumProducts,0)
            THEN 'Fourth' 
          ELSE 'Fifth' END) AS Quintile
FROM RankedCategories AS P1 
CROSS JOIN ProdCount
ORDER BY P1.ProductSales DESC;