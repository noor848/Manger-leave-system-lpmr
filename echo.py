"""
Simple Leave Management System with FastMCP
"""

from fastmcp import FastMCP
from datetime import datetime, timedelta

# Create MCP server
mcp = FastMCP("Leave Manager")

# In-memory storage (in real app, use database)
employees = {}
leave_requests = []
leave_balance = {}  # employee_id -> days_left

# ========== EMPLOYEE TOOLS ==========
@mcp.tool()
def register_employee(employee_id: str, name: str, email: str, department: str = "General") -> str:
    """Register a new employee"""
    if employee_id in employees:
        return f"Employee {employee_id} already exists!"
    
    employees[employee_id] = {
        "name": name,
        "email": email,
        "department": department,
        "join_date": datetime.now().strftime("%Y-%m-%d")
    }
    leave_balance[employee_id] = 20  # Default 20 days annual leave
    
    return f"✅ Employee {name} registered with ID: {employee_id}"

@mcp.tool()
def view_employee(employee_id: str) -> dict:
    """View employee details"""
    if employee_id not in employees:
        return {"error": f"Employee {employee_id} not found"}
    
    emp = employees[employee_id].copy()
    emp["leave_balance"] = leave_balance.get(employee_id, 0)
    return emp

# ========== LEAVE REQUEST TOOLS ==========
@mcp.tool()
def request_leave(employee_id: str, start_date: str, end_date: str, 
                 leave_type: str = "Annual", reason: str = "") -> dict:
    """Submit a leave request"""
    if employee_id not in employees:
        return {"error": f"Employee {employee_id} not found"}
    
    # Calculate days
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days_requested = (end - start).days + 1
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}
    
    # Check balance
    available = leave_balance.get(employee_id, 0)
    if days_requested > available:
        return {"error": f"Insufficient leave balance. Available: {available}, Requested: {days_requested}"}
    
    # Create request
    request_id = f"REQ{len(leave_requests)+1:03d}"
    request = {
        "request_id": request_id,
        "employee_id": employee_id,
        "employee_name": employees[employee_id]["name"],
        "start_date": start_date,
        "end_date": end_date,
        "days": days_requested,
        "leave_type": leave_type,
        "reason": reason,
        "status": "Pending",  # Pending, Approved, Rejected
        "submitted_date": datetime.now().strftime("%Y-%m-%d")
    }
    
    leave_requests.append(request)
    return {
        "message": "✅ Leave request submitted successfully!",
        "request_id": request_id,
        "details": request
    }

@mcp.tool()
def approve_leave(request_id: str, approver_id: str = "MANAGER") -> dict:
    """Approve a leave request"""
    for req in leave_requests:
        if req["request_id"] == request_id:
            if req["status"] != "Pending":
                return {"error": f"Request already {req['status']}"}
            
            # Deduct from balance
            emp_id = req["employee_id"]
            days_used = req["days"]
            leave_balance[emp_id] -= days_used
            
            req["status"] = "Approved"
            req["approved_by"] = approver_id
            req["approved_date"] = datetime.now().strftime("%Y-%m-%d")
            
            return {
                "message": "✅ Leave request approved!",
                "request": req
            }
    
    return {"error": f"Request {request_id} not found"}

@mcp.tool()
def reject_leave(request_id: str, reason: str = "", 
                approver_id: str = "MANAGER") -> dict:
    """Reject a leave request"""
    for req in leave_requests:
        if req["request_id"] == request_id:
            if req["status"] != "Pending":
                return {"error": f"Request already {req['status']}"}
            
            req["status"] = "Rejected"
            req["rejection_reason"] = reason
            req["rejected_by"] = approver_id
            req["rejected_date"] = datetime.now().strftime("%Y-%m-%d")
            
            return {
                "message": "❌ Leave request rejected",
                "request": req
            }
    
    return {"error": f"Request {request_id} not found"}

# ========== VIEW TOOLS ==========
@mcp.tool()
def check_balance(employee_id: str) -> dict:
    """Check leave balance"""
    if employee_id not in employees:
        return {"error": f"Employee {employee_id} not found"}
    
    return {
        "employee_id": employee_id,
        "employee_name": employees[employee_id]["name"],
        "leave_balance": leave_balance.get(employee_id, 0),
        "total_requests": len([r for r in leave_requests if r["employee_id"] == employee_id])
    }

@mcp.tool()
def view_all_requests(status: str = "All") -> list:
    """View all leave requests (filter by status if needed)"""
    if status.lower() == "all":
        return leave_requests
    else:
        return [req for req in leave_requests if req["status"].lower() == status.lower()]

@mcp.tool()
def view_my_requests(employee_id: str) -> list:
    """View leave requests for specific employee"""
    return [req for req in leave_requests if req["employee_id"] == employee_id]

# ========== ADMIN TOOLS ==========
@mcp.tool()
def add_leave_balance(employee_id: str, days: int) -> dict:
    """Add leave days to employee's balance"""
    if employee_id not in employees:
        return {"error": f"Employee {employee_id} not found"}
    
    leave_balance[employee_id] = leave_balance.get(employee_id, 0) + days
    
    return {
        "message": f"✅ Added {days} days to {employees[employee_id]['name']}'s balance",
        "employee": employees[employee_id]["name"],
        "new_balance": leave_balance[employee_id]
    }

@mcp.tool()
def department_summary(department: str = "All") -> dict:
    """Get leave summary by department"""
    result = {
        "department": department,
        "total_employees": 0,
        "total_leave_days": 0,
        "pending_requests": 0
    }
    
    for emp_id, emp in employees.items():
        if department.lower() == "all" or emp["department"].lower() == department.lower():
            result["total_employees"] += 1
            result["total_leave_days"] += leave_balance.get(emp_id, 0)
    
    result["pending_requests"] = len([r for r in leave_requests if r["status"] == "Pending"])
    return result

# ========== RESOURCES ==========
@mcp.resource("info://system")
def system_info():
    """Get system information"""
    return {
        "system": "Leave Management System",
        "version": "1.0.0",
        "total_employees": len(employees),
        "total_requests": len(leave_requests),
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@mcp.resource("help://tools")
def available_tools():
    """Get list of available tools"""
    return [
        {"name": "register_employee", "description": "Register new employee"},
        {"name": "request_leave", "description": "Submit leave request"},
        {"name": "approve_leave", "description": "Approve leave request"},
        {"name": "check_balance", "description": "Check leave balance"},
        {"name": "view_my_requests", "description": "View my leave requests"},
        {"name": "department_summary", "description": "Get department summary"}
    ]

# ========== DEMO SETUP ==========
def setup_demo_data():
    """Setup demo data for testing"""
    # Add demo employees
    register_employee("EMP001", "John Doe", "john@company.com", "Engineering")
    register_employee("EMP002", "Jane Smith", "jane@company.com", "HR")
    register_employee("EMP003", "Bob Wilson", "bob@company.com", "Sales")
    
    # Add some leave requests
    request_leave("EMP001", "2024-12-20", "2024-12-22", "Annual", "Family vacation")
    request_leave("EMP002", "2024-12-25", "2024-12-27", "Sick", "Medical appointment")
    
    # Approve one
    if leave_requests:
        approve_leave(leave_requests[0]["request_id"], "Admin")

# ========== RUN SERVER ==========
if __name__ == "__main__":
    # Setup demo data
    setup_demo_data()
    
    print("="*60)
    print("🏢 LEAVE MANAGEMENT SYSTEM")
    print("="*60)
    print(f"📊 Total Employees: {len(employees)}")
    print(f"📋 Total Leave Requests: {len(leave_requests)}")
    print("\n🛠️ Available Tools:")
    print("  • register_employee(id, name, email, department)")
    print("  • request_leave(employee_id, start_date, end_date, type, reason)")
    print("  • approve_leave(request_id, approver_id)")
    print("  • check_balance(employee_id)")
    print("  • view_my_requests(employee_id)")
    print("  • department_summary(department)")
    print("\n📦 Demo Employees:")
    for emp_id, emp in employees.items():
        print(f"   - {emp['name']} ({emp_id}): {leave_balance.get(emp_id, 0)} days left")
    
    print("\n🚀 Starting MCP Server...")
    print("="*60)
    
    mcp.run()
