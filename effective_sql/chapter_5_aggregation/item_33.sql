/*
problem: find max value of each group
*/

SELECT Category, Max(MaxABV) AS MaxAlcohol
FROM BeerStyles
GROUP BY Category;

/*
problem: for each category find the count which have max alcohol beverage
solution of the book: left join with the same table with on category and l.col < r.col. and filter l.col is null to get the max row
my solution: write cte to find beverage which is max in each category and then filter in the second query to get more information about their country 
*/
--this is wrong because it return max alcohold for combination of beverage and country
SELECT Category, Country, MAX(MaxABV) AS MaxAlcohol
FROM BeerStyles
GROUP BY Category, Country;


--find higesht beverage per category and it's origin contry
SELECT L.Category, L.Country, L.Style, L.MaxABV AS MaxAlcohol
FROM BeerStyles AS L LEFT JOIN BeerStyles AS R
  ON L.Category = R.Category
    AND L.MaxABV < R.MaxABV
WHERE R.MaxABV IS NULL
ORDER BY L.Category;

