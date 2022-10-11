/*
problem: using window function with additional syntax of row and range
row: specify the number of row in the window
range: specify the number of row in the window base on comparision with the current value
reference about row and range: https://learnsql.com/blog/difference-between-rows-range-window-functions/
*/
SELECT
  o.OrderNumber, o.CustomerID, o.OrderTotal,
  SUM(o.OrderTotal) OVER (
    PARTITION BY o.CustomerID
    ORDER BY o.OrderNumber, o.CustomerID
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS TotalByCustomer,
  SUM(o.OrderTotal) OVER (
    PARTITION BY o.CustomerID
    --RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS TotalOverall
FROM Orders AS o
ORDER BY o.OrderNumber, o.CustomerID;

/*
problem:
using lag(col, number) over(partition by customerid, month order by year) to find the data point of last year for the same customerid in the same month
using lead(col, number) over(partition by customerid, month order by year) to find the data point of next year for the same customer in the same month
using avg(col) over(partition by customerid, month order by year row betweent 1 preceding and 1 following) to compute aver of monthly customer perchase with 3 year.
or each window have three row (last year, current year, next year data point) to compute moving average
*/

WITH PurchaseStatistics AS (
	SELECT 
		p.CustomerID,
		YEAR(p.PurchaseDate) AS PurchaseYear,
		MONTH(p.PurchaseDate) AS PurchaseMonth,
		SUM(p.PurchaseAmount) AS PurchaseTotal,
		COUNT(p.PurchaseID) AS PurchaseCount
	FROM Purchases AS p
	GROUP BY 
		p.CustomerID, 
		YEAR(p.PurchaseDate),
		MONTH(p.PurchaseDate)
)
SELECT
  s.CustomerID, s.PurchaseYear, s.PurchaseMonth,
  LAG(s.PurchaseTotal, 1) OVER (
    PARTITION BY s.CustomerID, s.PurchaseMonth
    ORDER BY s.PurchaseYear
    ) AS PreviousMonthTotal,
  s.PurchaseTotal AS CurrentMonthTotal,
  LEAD(s.PurchaseTotal, 1) OVER (
    PARTITION BY s.CustomerID, s.PurchaseMonth
    ORDER BY s.PurchaseYear
    ) AS NextMonthTotal,
  AVG(s.PurchaseTotal) OVER (
    PARTITION BY s.CustomerID, s.PurchaseMonth
    ORDER BY s.PurchaseYear
    ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
    ) AS MonthOfYearAverage
FROM PurchaseStatistics AS s
ORDER BY s.CustomerID, s.PurchaseYear, s.PurchaseMonth;

/*
problem: find the different between range and row syntax of window function.
analyze:
    because the diffent how range vs row define now of row in the window. in this case we have with range the same customer id will have the same calculated value
*/
WITH PurchaseStatistics AS (
	SELECT 
		p.CustomerID,
		YEAR(p.PurchaseDate) AS PurchaseYear,
		MONTH(p.PurchaseDate) AS PurchaseMonth,
		SUM(p.PurchaseAmount) AS PurchaseTotal,
		COUNT(p.PurchaseID) AS PurchaseCount
	FROM Purchases AS p
	GROUP BY 
		p.CustomerID, 
		YEAR(p.PurchaseDate),
		MONTH(p.PurchaseDate)
)
SELECT
  s.CustomerID, s.PurchaseYear, s.PurchaseMonth,
  SUM(s.PurchaseCount) OVER (
    PARTITION BY s.PurchaseYear
    ORDER BY s.CustomerID
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS CountByRange,
  SUM(s.PurchaseCount) OVER (
    PARTITION BY s.PurchaseYear
    ORDER BY s.CustomerID
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS CountByRows
FROM PurchaseStatistics AS s
ORDER BY s.CustomerID, s.PurchaseYear, s.PurchaseMonth;