
/*
problem: StudentGrade(student, subject, final_grade), continuous range and criteria table, count number of student in each subject and point criteria
*/
--find student, subject, points
WITH StudentGrades (Student, Subject, FinalGrade) 
AS
(
  SELECT Stu.StudentFirstNM AS Student, Sub.SubjectNM AS Subject, SS.FinalGrade
  FROM StudentSubjects AS SS INNER JOIN Students AS Stu 
    ON SS.StudentID = Stu.StudentID
  INNER JOIN Subjects AS Sub
    ON SS.SubjectID = Sub.SubjectID
)--assign criteria to student
SELECT SG.Subject, GR.LetterGrade, COUNT(*) AS NumberOfStudents
FROM StudentGrades AS SG INNER JOIN GradeRangesContinuous AS GR 
  ON SG.FinalGrade >= GR.LowGradePoint
  AND SG.FinalGrade < GR.HighGradePoint 
GROUP BY SG.Subject, GR.LetterGrade --group by to count number of student in group
ORDER BY SG.Subject, GR.LetterGrade;