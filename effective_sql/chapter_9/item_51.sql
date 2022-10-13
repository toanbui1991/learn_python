/*
problem: generate null row
solution:
    one: generate index table
    two: generate empty row with union all
*/
WITH SeqNumTbl AS 
  (SELECT 1 AS SeqNum
   UNION ALL
   SELECT SeqNum + 1
   FROM SeqNumTbl
   WHERE SeqNum < 100),
SeqList AS
  (SELECT SeqNum 
   FROM SeqNumTbl)

SELECT ' ' AS CustName, ' ' AS CustStreetAddress, 
    ' ' AS CustCityState, ' ' AS CustZipCode
FROM SeqList
WHERE SeqNum <= 3
UNION ALL
SELECT CONCAT(C.CustFirstName, ' ', C.CustLastName) AS CustName,
    C.CustStreetAddress,
    CONCAT(C.CustCity, ', ', C.CustState, ' ', C.CustZipCode) 
       AS CustCityState, C.CustZipCode
FROM Customers AS C
ORDER BY CustZipCode;

/*
create a function which return a talbe with n row of blank
*/
CREATE FUNCTION MailingLabels (@skip AS int = 0)
RETURNS Table
AS RETURN
(SELECT ' ' AS CustName, ' ' AS CustStreetAddress, 
    ' ' AS CustCityState, ' ' AS CustZipCode
FROM ztblSeqNumbers --sequence table
WHERE Sequence <= @skip
UNION ALL
SELECT  
    CONCAT(C.CustFirstName, ' ', C.CustLastName) AS CustName,
    C.CustStreetAddress,
    CONCAT(C.CustCity, ', ', C.CustState, ' ', C.CustZipCode) 
       AS CustCityState, C.CustZipCode
FROM Customers AS C);
GO

SELECT * FROM MailingLabels(5)
ORDER BY CustZipCode;