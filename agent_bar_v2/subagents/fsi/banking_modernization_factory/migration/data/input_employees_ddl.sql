CREATE TABLE employees (
    employee_id    NUMBER(10)          PRIMARY KEY,
    first_name     VARCHAR2(50)        NOT NULL,
    last_name      VARCHAR2(50)        NOT NULL,
    email          VARCHAR2(100)       UNIQUE,
    hire_date      DATE                DEFAULT SYSDATE,
    salary         NUMBER(10, 2)       CHECK (salary > 0),
    department_id  NUMBER(5),
    -- Foreign Key Constraint
    CONSTRAINT fk_department
        FOREIGN KEY (department_id) 
        REFERENCES departments(department_id)
);
