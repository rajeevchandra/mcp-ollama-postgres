CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT,
    salary INTEGER
);

INSERT INTO employees (name, department, salary) VALUES
('Alice Johnson', 'Engineering', 95000),
('Bob Smith', 'Marketing', 72000),
('Carol White', 'Sales', 68000),
('David Brown', 'Engineering', 99000),
('Eva Green', 'HR', 63000)
ON CONFLICT DO NOTHING;
