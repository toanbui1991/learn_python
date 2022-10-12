/*
problem: count number of recipe in recipe class
analyze: count(*) will cause error because count(*) also count null value
*/

--the wrong approach with count(*)
SELECT Recipe_Classes.RecipeClassDescription, 
  COUNT(*) AS RecipeCount --this will cause wrong anwser
FROM Recipe_Classes 
  LEFT OUTER JOIN Recipes 
    ON Recipe_Classes.RecipeClassID = Recipes.RecipeClassID
GROUP BY Recipe_Classes.RecipeClassDescription;

--the correct approach with count(expression)
SELECT Recipe_Classes.RecipeClassDescription, 
COUNT(Recipes.RecipeClassID) AS RecipeCount --this will return correct answer
FROM Recipe_Classes 
  LEFT OUTER JOIN Recipes 
    ON Recipe_Classes.RecipeClassID = Recipes.RecipeClassID
GROUP BY Recipe_Classes.RecipeClassDescription;

-- the second approach with correlated subquery
SELECT Recipe_Classes.RecipeClassDescription, 
  (SELECT COUNT(Recipes.RecipeClassID) 
   FROM Recipes
   WHERE Recipes.RecipeClassID = Recipe_Classes.RecipeClassID) 
    AS RecipeCount
FROM Recipe_Classes