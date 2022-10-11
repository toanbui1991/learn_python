/*
problem: find recipes which use both beef an garlic as ingredient (using inner join to solve the problem)
*/

SELECT BeefRecipes.RecipeTitle
FROM 
  (SELECT Recipes.RecipeID, Recipes.RecipeTitle
   FROM (Recipes INNER JOIN Recipe_Ingredients
    ON Recipes.RecipeID = Recipe_Ingredients.RecipeID) 
      INNER JOIN Ingredients 
    ON Ingredients.IngredientID = 
      Recipe_Ingredients.IngredientID
   WHERE Ingredients.IngredientName = 'Beef') 
      AS BeefRecipes
  INNER JOIN
  (SELECT Recipe_Ingredients.RecipeID
   FROM Recipe_Ingredients INNER JOIN Ingredients
    ON Ingredients.IngredientID = 
      Recipe_Ingredients.IngredientID
   WHERE Ingredients.IngredientName = 'Garlic') 
      AS GarlicRecipes 
    ON BeefRecipes.RecipeID = GarlicRecipes.RecipeID;


/*
problem:  using exists keyword to check the exists of data point
*/
SELECT Customers.CustomerID, Customers.CustFirstName, 
  Customers.CustLastName, Orders.OrderNumber, Orders.OrderDate
FROM Customers
  INNER JOIN Orders
    ON Customers.CustomerID = Orders.CustomerID
WHERE EXISTS 
  (SELECT NULL
   FROM (Orders AS O2
      INNER JOIN Order_Details
        ON O2.OrderNumber = Order_Details.OrderNumber)
      INNER JOIN Products
        ON Products.ProductNumber = Order_Details.ProductNumber 
   WHERE Products.ProductName LIKE '%Skateboard%' 
    AND O2.OrderNumber = Orders.OrderNumber)
AND EXISTS 
  (SELECT NULL
   FROM (Orders AS O3 
      INNER JOIN Order_Details
        ON O3.OrderNumber = Order_Details.OrderNumber)
      INNER JOIN Products
        ON Products.ProductNumber = Order_Details.ProductNumber 
   WHERE Products.ProductName LIKE '%Helmet%'
      AND O3.OrderNumber = Orders.OrderNumber);


/*
problem: find product which have not been purchase in a period
*/
SELECT Products.ProductName
FROM Products
WHERE Products.ProductNumber NOT IN 
  (SELECT Order_Details.ProductNumber 
   FROM Orders 
      INNER JOIN Order_Details
        ON Orders.OrderNumber = Order_Details.OrderNumber
   WHERE Orders.OrderDate 
    BETWEEN '2015-12-01' AND '2015-12-31');

/*
problem: using case when test then result_one else result_two
*/
SELECT Employees.EmpFirstName, Employees.EmpLastName, 
  Customers.CustFirstName, Customers.CustLastName, 
  Customers.CustAreaCode, Customers.CustPhoneNumber, 
  (CASE WHEN Customers.CustomerID IN 
    (SELECT CustomerID 
     FROM Orders 
     WHERE Orders.EmployeeID = Employees.EmployeeID) 
        THEN 'Ordered from you.' 
        ELSE ' ' END) AS CustStatus
FROM Employees 
  INNER JOIN Customers
    ON Employees.EmpState = Customers.CustState;

/*
find the last date a product is orded or purchuse, 
note: in this solution, we use correlated subquery. other approach is subquery and join
*/
SELECT Products.ProductNumber, Products.ProductName, 
  (SELECT MAX(Orders.OrderDate) 
   FROM Orders 
      INNER JOIN Order_Details 
        ON Orders.OrderNumber = Order_Details.OrderNumber 
   WHERE Order_Details.ProductNumber = Products.ProductNumber) 
    AS LastOrder
FROM Products;