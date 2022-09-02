-- find students which have slary is lowery than her friends
-- this is correct because one student have only one best friend.
Select s.name FROM students s
INNER JOIN friends f ON f.id = s.id
INNER JOIN packages p on p.id = s.id
INNER JOIN packages p1 on p1.id = f.friend_id
where p.salary < p1.salary
order by p1.salary;