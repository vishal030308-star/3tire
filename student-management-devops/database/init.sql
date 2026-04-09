CREATE DATABASE students;

USE students;

CREATE TABLE student (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    tech VARCHAR(100),
    location VARCHAR(100)
);