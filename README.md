# 🏢 Leave Management System with FastMCP

A simple yet powerful leave management system built with FastMCP (Model Context Protocol). This system allows organizations to manage employee leave requests, approvals, and balances through an AI-powered interface.

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Available Tools](#available-tools)
- [API Reference](#api-reference)
- [Demo Data](#demo-data)
- [Architecture](#architecture)
- [Future Enhancements](#future-enhancements)

---

## ✨ Features

### Employee Management
- ✅ Register new employees with ID, name, email, and department
- ✅ View employee details and leave balances
- ✅ Track employee join dates

### Leave Request Management
- ✅ Submit leave requests with date ranges
- ✅ Support multiple leave types (Annual, Sick, etc.)
- ✅ Automatic leave balance validation
- ✅ Request approval/rejection workflow
- ✅ Track request status (Pending, Approved, Rejected)

### Leave Balance Tracking
- ✅ Automatic balance deduction on approval
- ✅ Real-time balance checking
- ✅ Admin tools to adjust balances

### Reporting & Analytics
- ✅ View all requests with status filtering
- ✅ Employee-specific request history
- ✅ Department-level summaries
- ✅ System-wide statistics

---

## 🔧 Prerequisites

- Python 3.8 or higher
- FastMCP library
- MCP-compatible AI client (Claude Desktop, etc.)

---

## 📦 Installation

### 1. Install Dependencies

```bash
pip install fastmcp
```

### 2. Clone or Download the Code

Save the leave management system code as `leave_manager.py`

### 3. Run the Server

```bash
python leave_manager.py
```

### 4. Connect to MCP Client

Add the following configuration to your MCP client settings (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "leave-manager": {
      "command": "python",
      "args": ["/path/to/leave_manager.py"]
    }
  }
}
```

---

## ⚙️ Configuration

### Default Settings

- **Default Leave Balance**: 20 days per employee
- **Date Format**: YYYY-MM-DD (ISO 8601)
- **Storage**: In-memory (resets on restart)

### Customization

To modify default settings, edit the following in `leave_manager.py`:

```python
# Change default leave balance
leave_balance[employee_id] = 20  # Modify this value

# Add custom leave types
leave_type: str = "Annual"  # Can be "Annual", "Sick", "Personal", etc.
```

---

## 🚀 Usage

### Basic Workflow

#### 1. Register an Employee

```python
register_employee(
    employee_id="EMP004",
    name="Alice Johnson",
    email="alice@company.com",
    department="Marketing"
)
```

#### 2. Submit a Leave Request

```python
request_leave(
    employee_id="EMP004",
    start_date="2024-12-25",
    end_date="2024-12-27",
    leave_type="Annual",
    reason="Holiday vacation"
)
```

#### 3. Check Leave Balance

```python
check_balance(employee_id="EMP004")
```

#### 4. Approve/Reject Request

```python
# Approve
approve_leave(request_id="REQ001", approver_id="MANAGER")

# Reject
reject_leave(request_id="REQ002", reason="Insufficient coverage", approver_id="MANAGER")
```

#### 5. View Requests

```python
# View all requests
view_all_requests(status="All")

# View only pending requests
view_all_requests(status="Pending")

# View employee-specific requests
view_my_requests(employee_id="EMP004")
```

---

## 🛠️ Available Tools

### Employee Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `register_employee` | Register a new employee | `employee_id`, `name`, `email`, `department` |
| `view_employee` | View employee details | `employee_id` |

### Leave Operations

| Tool | Description | Parameters |
|------|-------------|------------|
| `request_leave` | Submit a leave request | `employee_id`, `start_date`, `end_date`, `leave_type`, `reason` |
| `approve_leave` | Approve a leave request | `request_id`, `approver_id` |
| `reject_leave` | Reject a leave request | `request_id`, `reason`, `approver_id` |
| `check_balance` | Check employee leave balance | `employee_id` |

### Viewing & Reporting

| Tool | Description | Parameters |
|------|-------------|------------|
| `view_all_requests` | View all leave requests | `status` (All/Pending/Approved/Rejected) |
| `view_my_requests` | View employee's requests | `employee_id` |
| `department_summary` | Get department statistics | `department` |

### Administration

| Tool | Description | Parameters |
|------|-------------|------------|
| `add_leave_balance` | Add leave days to employee | `employee_id`, `days` |

---

## 📚 API Reference

### Employee Registration

```python
register_employee(
    employee_id: str,      # Unique employee identifier
    name: str,             # Full name
    email: str,            # Email address
    department: str = "General"  # Department (optional)
) -> str
```

**Returns**: Success message with employee ID

### Leave Request Submission

```python
request_leave(
    employee_id: str,      # Employee ID
    start_date: str,       # Start date (YYYY-MM-DD)
    end_date: str,         # End date (YYYY-MM-DD)
    leave_type: str = "Annual",  # Leave type (optional)
    reason: str = ""       # Reason (optional)
) -> dict
```

**Returns**: Dictionary with request details and request ID

### Leave Approval

```python
approve_leave(
    request_id: str,           # Request ID to approve
    approver_id: str = "MANAGER"  # Approver ID (optional)
) -> dict
```

**Returns**: Dictionary with approval confirmation

### Balance Check

```python
check_balance(employee_id: str) -> dict
```

**Returns**: Dictionary with employee name, balance, and total requests

---

## 🎭 Demo Data

The system comes with pre-loaded demo data:

### Demo Employees

| ID | Name | Email | Department | Leave Balance |
|----|------|-------|------------|---------------|
| EMP001 | John Doe | john@company.com | Engineering | 17 days |
| EMP002 | Jane Smith | jane@company.com | HR | 20 days |
| EMP003 | Bob Wilson | bob@company.com | Sales | 20 days |

### Demo Requests

- **REQ001**: John Doe - Dec 20-22, 2024 (Approved)
- **REQ002**: Jane Smith - Dec 25-27, 2024 (Pending)

---

## 🏗️ Architecture

### Data Structure

```
employees = {
    "EMP001": {
        "name": "John Doe",
        "email": "john@company.com",
        "department": "Engineering",
        "join_date": "2024-12-19"
    }
}

leave_balance = {
    "EMP001": 17  # Days remaining
}

leave_requests = [
    {
        "request_id": "REQ001",
        "employee_id": "EMP001",
        "employee_name": "John Doe",
        "start_date": "2024-12-20",
        "end_date": "2024-12-22",
        "days": 3,
        "leave_type": "Annual",
        "reason": "Family vacation",
        "status": "Approved",
        "submitted_date": "2024-12-19",
        "approved_by": "Admin",
        "approved_date": "2024-12-19"
    }
]
