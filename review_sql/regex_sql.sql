-- problem: find a list of city start with vowel.
-- learning:
  --one: regex test syntax in msyql with regexp "test_condition"
select city from station
where city regexp "^[a, e, i, o, u]";

-- learning using distinct function to get unique value
select distinct city from station
where city regexp "[a, e, i, o, u]$";
-- learning about regex: . means match everything, * mean quantifier mathc zero or more
select distinct city from station 
where city regexp "^[a, e, i, o, u].*[a, e, i, o, u]$";
-- learning about not logic expression
select distinct city from station
where city not regexp "[a, e, i, o, u]$";
--learning: logical test with or, and
select distinct city from station
where city not regexp "^[a, e, i, o, u]"
or city not regexp "[a, e, i, o, u]$"
-- learning about and for multiple logical testing 
select distinct city from station
where city not regexp "^[a, e, i, o, u]"
and city not regexp "[a, e, i, o, u]$"
-- learning about string function in mysq. the function is rigth(column, int)
-- learning about order by with multiple columns. default order by is asc.
select name from students
where marks > 75
order by right(name, 3), id asc;
-- learn about avg function for number column type
select avg(population) from city
where district = "California";