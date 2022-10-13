/*
problem: find order in the last two month
analyze: there are two approach.
    one: the normal apporach
    two: create dimdate table and use it for datetime filter and calculation
*/
SELECT DATENAME(WEEKDAY, o.OrderDate) AS OrderDateWeekDay, 
  o.OrderDate,
  DATENAME(WEEKDAY, o.ShipDate) AS ShipDateWeekDay,
  o.ShipDate,
  DATEDIFF(DAY, o.OrderDate, o.ShipDate) AS DeliveryLead
FROM Orders AS o
WHERE o.OrderDate >= 
    DATEADD(MONTH, -2, DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1))
  AND o.OrderDate < DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)
;

--the second approach is use DimDate table
SELECT od.WeekDayNameLong AS OrderDateWeekDay, 
  o.OrderDate,
  sd.WeekDayNameLong AS ShipDateWeekDay,
  o.ShipDate,
  sd.DateKey - od.DateKey AS DeliveryLead
FROM Orders AS o
INNER JOIN DimDate AS od
  ON o.OrderDate = od.DateValue --to get delivery date key
INNER JOIN DimDate AS sd
  ON o.ShipDate = sd.DateValue --to get shiping date key
INNER JOIN DimDate AS td
  ON td.DateValue = CAST(GETDATE() AS date) --to get current date
WHERE od.MonthSeqNo = (td.MonthSeqNo - 1); --filter base on deliver date and dimdate table