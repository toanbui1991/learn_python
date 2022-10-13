
/*
problem: calculate total number of sale of group agent + month
*/
SELECT A.AgtFirstName, A.AgtLastName, 
    MONTH(E.StartDate) AS ContractMonth, 
    SUM(E.ContractPrice) AS TotalContractValue
FROM Agents AS A INNER JOIN Engagements AS E
  ON A.AgentID = E.AgentID
WHERE YEAR(E.StartDate) = 2015
GROUP BY A.AgtFirstName, A.AgtLastName, MONTH(E.StartDate);

/*
problem: present gent total sale with wide format
solution: using sum(condition)
*/
SELECT A.AgtFirstName, A.AgtLastName, 
    YEAR(E.StartDate) AS ContractYear,
    SUM(CASE WHEN MONTH(E.StartDate) = 1 
             THEN E.ContractPrice END) AS January,
    SUM(CASE WHEN MONTH(E.StartDate) = 2 
             THEN E.ContractPrice END) AS February,
    SUM(CASE WHEN MONTH(E.StartDate) = 3 
             THEN E.ContractPrice END) AS March,
    SUM(CASE WHEN MONTH(E.StartDate) = 4 
             THEN E.ContractPrice END) AS April,
    SUM(CASE WHEN MONTH(E.StartDate) = 5 
             THEN E.ContractPrice END) AS May,
    SUM(CASE WHEN MONTH(E.StartDate) = 6 
             THEN E.ContractPrice END) AS June,
    SUM(CASE WHEN MONTH(E.StartDate) = 7 
             THEN E.ContractPrice END) AS July,
    SUM(CASE WHEN MONTH(E.StartDate) = 8 
             THEN E.ContractPrice END) AS August,
    SUM(CASE WHEN MONTH(E.StartDate) = 9 
             THEN E.ContractPrice END) AS September,
    SUM(CASE WHEN MONTH(E.StartDate) = 10 
             THEN E.ContractPrice END) AS October,
    SUM(CASE WHEN MONTH(E.StartDate) = 11 
             THEN E.ContractPrice END) AS November,
    SUM(CASE WHEN MONTH(E.StartDate) = 12 
             THEN E.ContractPrice END) AS December
FROM Agents AS A LEFT JOIN
    (SELECT En.AgentID, En.StartDate, En.ContractPrice
     FROM Engagements AS En
     WHERE En.StartDate >= '2015-01-01'
       AND En.StartDate < '2016-01-01') AS E
  ON A.AgentID = E.AgentID
GROUP BY AgtFirstName, AgtLastName, YEAR(E.StartDate);

/*
problem: given tally table ztblQuarters , privot table
idea: is to assign each row of data point with index of 1 and 0 
*/
SELECT AE.AgtFirstName, AE.AgtLastName, z.YearNumber,
    SUM(AE.ContractPrice * Z.Qtr_1st) AS First_Quarter,
    SUM(AE.ContractPrice * Z.Qtr_2nd) AS Second_Quarter,
    SUM(AE.ContractPrice * Z.Qtr_3rd) AS Third_Quarter,
    SUM(AE.ContractPrice * Z.Qtr_4th) AS Fourth_Quarter
FROM ztblQuarters AS Z CROSS JOIN 
  (SELECT A.AgtFirstName, A.AgtLastName, 
       E.StartDate, E.ContractPrice
   FROM Agents AS A LEFT JOIN Engagements AS E
    ON A.AgentID = E.AgentID) AS AE
WHERE (AE.StartDate BETWEEN Z.QuarterStart AND Z.QuarterEnd)
   OR (AE.StartDate IS NULL AND Z.YearNumber = 2015)
GROUP BY AgtFirstName, AgtLastName, YearNumber;