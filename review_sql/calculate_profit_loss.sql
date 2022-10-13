/*
problem: compute profit or loss
analyze: profit_loss = sell price - buy price therefore use sum(iif(type == 'Buy'), -1*price, price)
*/
select
stock_name 
,sum(
    iif(operation = 'Buy', -1*price, price)
) as capital_gain_loss
from stocks
group by stock_name