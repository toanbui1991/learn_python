/*
problem: given criteria table (ztblPurchaseCoupons), tally table (sequence index table)
    one: calculate number of coupon base on customer purchase
    two: for each customer, create number of row equal with number of couple
solution:
    one: aggregate customer purcahse
    two: left join with between and to get criteria (number of coupon)
    three: cross join and filter with where r.sequence <= l.num_coupon
why this step three work:
    - each row in the left will have n row in the right so we limit the number of row with l.num_copun >= r.sequence (filter out other row)
*/
WITH CustDecPurch AS --compute customer total purchase value
(SELECT Orders.CustomerID, 
   SUM((QuotedPrice)*(QuantityOrdered)) AS Purchase 
 FROM Orders INNER JOIN Order_Details
   ON Orders.OrderNumber = Order_Details.OrderNumber 
 WHERE Orders.OrderDate Between '2015-12-01'
     AND '2015-12-31' 
 GROUP BY Orders.CustomerID),
 Coupons AS --assign criteria or number of couple base on total purchase for each customer
(SELECT CustDecPurch.CustomerID, ztblPurchaseCoupons.NumCoupons
 FROM CustDecPurch CROSS JOIN ztblPurchaseCoupons
 WHERE CustDecPurch.Purchase BETWEEN 
   ztblPurchaseCoupons.LowSpend AND 
   ztblPurchaseCoupons.HighSpend)

SELECT C.CustFirstName, C.CustLastName, C.CustStreetAddress, 
     C.CustCity, C.CustState, C.CustZipCode, CP.NumCoupons
FROM Coupons AS CP INNER JOIN Customers AS C
  ON CP.CustomerID = C.CustomerID
CROSS JOIN ztblSeqNumbers AS z --
WHERE z.Sequence <= CP.NumCoupons;