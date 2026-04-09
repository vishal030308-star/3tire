


3-tier app is divided into:
Frontend → HTML, CSS, JS (static)
Backend → Python + Flask
Database → MySQL
Web Server → Nginx
DevOps Tools → Docker + Jenkins

Frontend running on: 127.0.0.1:5500
Backend running on: localhost:5000

Sql data show:
docker exec -it student-management-devops_db_1 mysql -u root -p
(password = root)
USE students;
SELECT * FROM student;