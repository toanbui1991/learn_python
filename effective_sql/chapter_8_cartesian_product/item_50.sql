/*
problem: find entertainer who have all customer style (entertainer style will match customer style )
solution:
    one: find combination of artist and their style
    two: find combination of customer and their style
    three: jon one and two by style key. group by customer and artist to counter number of commen style of customer and artist.
    four: compare between three (number of commnet style between customer and aritest) with the number of style of the customer
*/
WITH CustStyles AS --customer and their style
  (SELECT C.CustomerID, C.CustFirstName, 
      C.CustLastName, MS.StyleName
   FROM Customers AS C INNER JOIN Musical_Preferences AS MP
     ON C.CustomerID = MP.CustomerID
   INNER JOIN Musical_Styles AS MS
     ON MP.StyleID = MS.StyleID),

EntStyles AS -- entertainer and their style
  (SELECT E.EntertainerID, E.EntStageName, MS.StyleName
   FROM Entertainers AS E INNER JOIN Entertainer_Styles AS ES
     ON E.EntertainerID = ES.EntertainerID
   INNER JOIN Musical_Styles AS MS
     ON ES.StyleID = MS.StyleID)

SELECT CustStyles.CustomerID, CustStyles.CustFirstName, 
    CustStyles.CustLastName, EntStyles.EntStageName
FROM CustStyles INNER JOIN EntStyles
  ON CustStyles.StyleName = EntStyles.StyleName
  -- group by both customer and artist
GROUP BY CustStyles.CustomerID, CustStyles.CustFirstName,
     CustStyles.CustLastName, EntStyles.EntStageName
HAVING COUNT(EntStyles.StyleName) = --number of style an artist have which is also have in customer, check with number of style customer have
  (SELECT COUNT(StyleName) 
   FROM CustStyles AS CS1
   WHERE CS1.CustomerID = CustStyles.CustomerID)


/*
problem: given
    one: customer and their style reference(customer, style, rank of style)
    two: artist and their style strength(artist, style, rank of style strength)
    find artist which have their stop style match with customer top two love style
solution:
    one: find customer, style and customer-style refernece with 
    two: find artist, style and artiest-style strength
    three: cross join between one and two and then filter with where to match condition
*/

WITH CustPreferences AS --get customer and style but with reference column (1, 2, 3)
(SELECT C.CustomerID, C.CustFirstName, C.CustLastName, 
       MAX((CASE WHEN MP.PreferenceSeq = 1  
                 THEN MP.StyleID 
                 ELSE Null END)) AS FirstPreference,
       MAX((CASE WHEN MP.PreferenceSeq = 2  
                 THEN MP.StyleID 
                 ELSE Null END)) AS SecondPreference,
       MAX((CASE WHEN MP.PreferenceSeq = 3  
                 THEN MP.StyleID 
                 ELSE Null END)) AS ThirdPreference
   FROM Musical_Preferences AS MP INNER JOIN Customers AS C
      ON MP.CustomerID = C.CustomerID 
   GROUP BY C.CustomerID, C.CustFirstName, C.CustLastName),

EntStrengths AS --get artiest and their style with strength reference col
(SELECT E.EntertainerID, E.EntStageName, 
       MAX((CASE WHEN ES.StyleStrength = 1 
                 THEN ES.StyleID 
                 ELSE Null END)) AS FirstStrength, 
       MAX((CASE WHEN ES.StyleStrength = 2 
                 THEN ES.StyleID 
                 ELSE Null END)) AS SecondStrength, 
       MAX((CASE WHEN ES.StyleStrength = 3 
                 THEN ES.StyleID 
                 ELSE Null END)) AS ThirdStrength 
   FROM Entertainer_Styles AS ES
   INNER JOIN Entertainers AS E
      ON ES.EntertainerID = E.EntertainerID 
   GROUP BY E.EntertainerID, E.EntStageName)

SELECT CustomerID, CustFirstName, CustLastName, 
   EntertainerID, EntStageName
FROM CustPreferences CROSS JOIN EntStrengths
WHERE (FirstPreference = FirstStrength
       AND SecondPreference = SecondStrength)
   OR (SecondPreference =FirstStrength
       AND FirstPreference = SecondStrength)
ORDER BY CustomerID;