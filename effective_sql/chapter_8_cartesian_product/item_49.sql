/*
problem: given a set find combination of all element in that set. two element have to be different 
we can not have (1, 1). and (1, 2) is the same as (2,1)
*/

SELECT Teams1.TeamID AS Team1ID, Teams1.TeamName AS Team1Name,
Teams2.TeamID AS Team2ID, Teams2.TeamName AS Team2Name
FROM Teams AS Teams1 CROSS JOIN Teams AS Teams2
WHERE Teams2.TeamID > Teams1.TeamID -- condition for cartesian product
ORDER BY Teams1.TeamID, Teams2.TeamID;