
/*
problem: find main course which have less than 3 spices
analyze: with the aggregate and then filter with aggregate result with < number, we can have error result with missing zero case.
    one: aggregate and then filter (recipe class + ingredient class spices and and less than 3) 
    two: left join to avoid missing zero and handle null to 0 (filter the recipe with receip class is main course)
note: in this problem we have two filter criteria the main table have to fileter recipe class =
*/
SELECT Recipes.RecipeTitle, 
  COUNT(Recipe_Ingredients.RecipeID) AS IngredCount
FROM (((Recipe_Classes 
  INNER JOIN Recipes
    ON Recipe_Classes.RecipeClassID = Recipes.RecipeClassID) 
  INNER JOIN Recipe_Ingredients
    ON Recipes.RecipeID = Recipe_Ingredients.RecipeID)
  INNER JOIN Ingredients
    ON Recipe_Ingredients.IngredientID = 
    Ingredients.IngredientID)
  INNER JOIN Ingredient_Classes 
    ON Ingredients.IngredientClassID = 
    Ingredient_Classes.IngredientClassID
WHERE Recipe_Classes.RecipeClassDescription = 'Main Course' 
  AND Ingredient_Classes.IngredientClassDescription = 'Spice'
GROUP BY Recipes.RecipeTitle
HAVING COUNT(Recipe_Ingredients.RecipeID) < 3;


SELECT Recipes.RecipeTitle, 
  COUNT(RI.RecipeID) AS IngredCount
FROM (Recipe_Classes 
  INNER JOIN Recipes
    ON Recipe_Classes.RecipeClassID = Recipes.RecipeClassID) 
  LEFT OUTER JOIN
     (SELECT Recipe_Ingredients.RecipeID, 
         Ingredient_Classes.IngredientClassDescription
      FROM (Recipe_Ingredients
        INNER JOIN Ingredients
          ON Recipe_Ingredients.IngredientID = 
      Ingredients.IngredientID) 
        INNER JOIN Ingredient_Classes 
          ON Ingredients.IngredientClassID = 
         Ingredient_Classes.IngredientClassID) AS RI
    ON Recipes.RecipeID = RI.RecipeID AND RI.IngredientClassDescription = 'Spice' 
WHERE Recipe_Classes.RecipeClassDescription = 'Main course' 
GROUP BY Recipes.RecipeTitle
HAVING COUNT(RI.RecipeID) < 3;


SELECT Recipes.RecipeTitle, 
  COUNT(RI.RecipeID) AS IngredCount
FROM (Recipe_Classes 
  INNER JOIN Recipes
    ON Recipe_Classes.RecipeClassID = Recipes.RecipeClassID) 
  LEFT OUTER JOIN
  (SELECT Recipe_Ingredients.RecipeID, 
    Ingredient_Classes.IngredientClassDescription
   FROM (Recipe_Ingredients
    INNER JOIN Ingredients
      ON Recipe_Ingredients.IngredientID = 
       Ingredients.IngredientID) 
    INNER JOIN Ingredient_Classes 
      ON Ingredients.IngredientClassID = 
       Ingredient_Classes.IngredientClassID
   WHERE 
     Ingredient_Classes.IngredientClassDescription = 'Spice') 
    AS RI
      ON Recipes.RecipeID = RI.RecipeID 
WHERE Recipe_Classes.RecipeClassDescription = 'Main course' 
GROUP BY Recipes.RecipeTitle
HAVING COUNT(RI.RecipeID) < 3;