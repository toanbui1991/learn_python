/*
problem: calculate running sum, reference to the book for result visualization
*/
SELECT
  o.OrderNumber, o.CustomerID, o.OrderTotal,
  SUM(o.OrderTotal) OVER (
    PARTITION BY o.CustomerID
    ORDER BY o.OrderNumber, o.CustomerID
    ) AS TotalByCustomer,
  SUM(o.OrderTotal) OVER (
    ORDER BY o.OrderNumber
    ) AS TotalOverall
FROM Orders AS o
ORDER BY o.OrderNumber, o.CustomerID;

/*
compute reverse running sum (window range reduced)
in example: reverse running sum - data point value
*/

SELECT 
  t.AccountID, t.Amount,
  SUM(t.Amount) OVER (
    PARTITION BY t.AccountID
    ORDER BY t.TransactionID DESC
    ) - t.Amount AS TotalUnspent,
  SUM(t.Amount) OVER (
    ORDER BY t.TransactionID
    ) AS TotalOverall
FROM Transactions AS t
ORDER BY t.TransactionID;