{
    "name": "Employee Late Check-In Deductions",
    "version": "18.0.1.0.0",
    "description": "Employee Lateness Deductions",
    'author':       "SOFT TECH LTD",
    "website":      "softatt.com",
    "license": "OPL-1",
    "category": "hr",
    "depends": ["softatt_attendance", "hr_contract"],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/attendance_rule.xml",
        "views/hr_attendance.xml",
        "views/hr_employee.xml",
    ],
}
