"""
Leave Management System with RAG (FastMCP Cloud)
A complete leave management system with document Q&A capabilities
"""

from fastmcp import FastMCP
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import json

# Initialize FastMCP server
mcp = FastMCP("Leave Management RAG")

# ========== DATA STORES ==========
employees = {}
leave_requests = []
leave_balance = {}
knowledge_base = {}  # Simple document store for RAG

# ========== KNOWLEDGE BASE / RAG SYSTEM ==========

@mcp.tool()
def add_policy_document(
    policy_id: str,
    title: str,
    content: str,
    category: str = "General"
) -> dict:
    """
    Add a policy document to the knowledge base for RAG retrieval.
    Categories: General, Annual, Sick, Emergency, Remote, Benefits
    """
    knowledge_base[policy_id] = {
        "policy_id": policy_id,
        "title": title,
        "content": content,
        "category": category,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "word_count": len(content.split())
    }
    
    return {
        "message": f"✅ Policy '{title}' added to knowledge base",
        "policy_id": policy_id,
        "category": category,
        "word_count": len(content.split())
    }

@mcp.tool()
def search_policies(
    query: str,
    category: Optional[str] = None,
    max_results: int = 3
) -> List[dict]:
    """
    Search policy documents using simple keyword matching (RAG retrieval).
    This simulates semantic search for demo purposes.
    """
    query_lower = query.lower()
    results = []
    
    for policy_id, doc in knowledge_base.items():
        # Filter by category if specified
        if category and doc["category"].lower() != category.lower():
            continue
        
        # Simple keyword matching (in production, use embeddings)
        content_lower = doc["content"].lower()
        title_lower = doc["title"].lower()
        
        # Calculate simple relevance score
        score = 0
        query_words = query_lower.split()
        
        for word in query_words:
            if word in title_lower:
                score += 10  # Title matches are more important
            if word in content_lower:
                score += content_lower.count(word)
        
        if score > 0:
            results.append({
                "policy_id": policy_id,
                "title": doc["title"],
                "category": doc["category"],
                "relevance_score": score,
                "excerpt": doc["content"][:300] + "..." if len(doc["content"]) > 300 else doc["content"],
                "full_content": doc["content"]
            })
    
    # Sort by relevance
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    return results[:max_results]

@mcp.tool()
def ask_policy_question(question: str, category: Optional[str] = None) -> dict:
    """
    Ask a question about leave policies (RAG-powered Q&A).
    The system will search relevant documents and provide an answer.
    """
    # Search for relevant documents
    relevant_docs = search_policies(question, category, max_results=3)
    
    if not relevant_docs:
        return {
            "answer": "I couldn't find any relevant policy documents for your question.",
            "sources": [],
            "confidence": "low"
        }
    
    # Construct context from retrieved documents
    context = "\n\n".join([
        f"[{doc['title']}]\n{doc['full_content']}"
        for doc in relevant_docs
    ])
    
    # Generate answer based on context (simplified version)
    # In production, you'd use an LLM here with the context
    answer = f"Based on the available policies, here's what I found:\n\n"
    
    for i, doc in enumerate(relevant_docs, 1):
        answer += f"{i}. From '{doc['title']}' ({doc['category']}):\n"
        answer += f"   {doc['excerpt']}\n\n"
    
    return {
        "question": question,
        "answer": answer,
        "sources": [{"title": doc["title"], "policy_id": doc["policy_id"]} for doc in relevant_docs],
        "confidence": "high" if len(relevant_docs) >= 2 else "medium",
        "context_used": context
    }

@mcp.tool()
def list_all_policies(category: Optional[str] = None) -> List[dict]:
    """List all policy documents in the knowledge base"""
    policies = list(knowledge_base.values())
    
    if category:
        policies = [p for p in policies if p["category"].lower() == category.lower()]
    
    return [{
        "policy_id": p["policy_id"],
        "title": p["title"],
        "category": p["category"],
        "word_count": p["word_count"],
        "created_at": p["created_at"]
    } for p in policies]

@mcp.tool()
def get_policy_by_id(policy_id: str) -> dict:
    """Retrieve a specific policy document by ID"""
    if policy_id not in knowledge_base:
        return {"error": f"Policy {policy_id} not found"}
    
    return knowledge_base[policy_id]

# ========== EMPLOYEE MANAGEMENT ==========

@mcp.tool()
def register_employee(
    employee_id: str,
    name: str,
    email: str,
    department: str = "General"
) -> dict:
    """Register a new employee in the system"""
    if employee_id in employees:
        return {"error": f"Employee {employee_id} already exists!"}
    
    employees[employee_id] = {
        "employee_id": employee_id,
        "name": name,
        "email": email,
        "department": department,
        "join_date": datetime.now().strftime("%Y-%m-%d"),
        "status": "Active"
    }
    leave_balance[employee_id] = 20  # Default 20 days annual leave
    
    return {
        "message": f"✅ Employee {name} registered successfully",
        "employee_id": employee_id,
        "initial_leave_balance": 20
    }

@mcp.tool()
def view_employee(employee_id: str) -> dict:
    """View employee details including leave balance"""
    if employee_id not in employees:
        return {"error": f"Employee {employee_id} not found"}
    
    emp = employees[employee_id].copy()
    emp["leave_balance"] = leave_balance.get(employee_id, 0)
    
    # Add request statistics
    emp_requests = [r for r in leave_requests if r["employee_id"] == employee_id]
    emp["total_requests"] = len(emp_requests)
    emp["pending_requests"] = len([r for r in emp_requests if r["status"] == "Pending"])
    emp["approved_requests"] = len([r for r in emp_requests if r["status"] == "Approved"])
    
    return emp

@mcp.tool()
def list_all_employees(department: Optional[str] = None) -> List[dict]:
    """List all employees, optionally filtered by department"""
    emp_list = list(employees.values())
    
    if department:
        emp_list = [e for e in emp_list if e["department"].lower() == department.lower()]
    
    # Add leave balance to each
    for emp in emp_list:
        emp["leave_balance"] = leave_balance.get(emp["employee_id"], 0)
    
    return emp_list

# ========== LEAVE REQUEST MANAGEMENT ==========

@mcp.tool()
def request_leave(
    employee_id: str,
    start_date: str,
    end_date: str,
    leave_type: str = "Annual",
    reason: str = ""
) -> dict:
    """
    Submit a leave request.
    Leave types: Annual, Sick, Emergency, Unpaid
    Date format: YYYY-MM-DD
    """
    if employee_id not in employees:
        return {"error": f"Employee {employee_id} not found"}
    
    # Calculate days
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days_requested = (end - start).days + 1
        
        if days_requested <= 0:
            return {"error": "End date must be after start date"}
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}
    
    # Check balance for Annual leave
    if leave_type.lower() == "annual":
        available = leave_balance.get(employee_id, 0)
        if days_requested > available:
            return {
                "error": f"Insufficient leave balance. Available: {available}, Requested: {days_requested}"
            }
    
    # Create request
    request_id = f"REQ{len(leave_requests)+1:04d}"
    request = {
        "request_id": request_id,
        "employee_id": employee_id,
        "employee_name": employees[employee_id]["name"],
        "start_date": start_date,
        "end_date": end_date,
        "days": days_requested,
        "leave_type": leave_type,
        "reason": reason,
        "status": "Pending",
        "submitted_date": datetime.now().strftime("%Y-%m-%d"),
        "approved_by": None,
        "approved_date": None
    }
    
    leave_requests.append(request)
    
    return {
        "message": "✅ Leave request submitted successfully!",
        "request_id": request_id,
        "employee": employees[employee_id]["name"],
        "dates": f"{start_date} to {end_date}",
        "days": days_requested,
        "status": "Pending"
    }

@mcp.tool()
def approve_leave(request_id: str, approver_id: str = "MANAGER") -> dict:
    """Approve a pending leave request"""
    for req in leave_requests:
        if req["request_id"] == request_id:
            if req["status"] != "Pending":
                return {"error": f"Request is already {req['status']}"}
            
            # Deduct from balance (for Annual leave)
            if req["leave_type"].lower() == "annual":
                emp_id = req["employee_id"]
                leave_balance[emp_id] -= req["days"]
            
            req["status"] = "Approved"
            req["approved_by"] = approver_id
            req["approved_date"] = datetime.now().strftime("%Y-%m-%d")
            
            return {
                "message": "✅ Leave request approved!",
                "request_id": request_id,
                "employee": req["employee_name"],
                "days": req["days"],
                "new_balance": leave_balance.get(req["employee_id"], 0)
            }
    
    return {"error": f"Request {request_id} not found"}

@mcp.tool()
def reject_leave(
    request_id: str,
    reason: str = "",
    approver_id: str = "MANAGER"
) -> dict:
    """Reject a pending leave request"""
    for req in leave_requests:
        if req["request_id"] == request_id:
            if req["status"] != "Pending":
                return {"error": f"Request is already {req['status']}"}
            
            req["status"] = "Rejected"
            req["rejection_reason"] = reason
            req["rejected_by"] = approver_id
            req["rejected_date"] = datetime.now().strftime("%Y-%m-%d")
            
            return {
                "message": "❌ Leave request rejected",
                "request_id": request_id,
                "employee": req["employee_name"],
                "reason": reason
            }
    
    return {"error": f"Request {request_id} not found"}

@mcp.tool()
def check_balance(employee_id: str) -> dict:
    """Check leave balance for an employee"""
    if employee_id not in employees:
        return {"error": f"Employee {employee_id} not found"}
    
    emp_requests = [r for r in leave_requests if r["employee_id"] == employee_id]
    
    return {
        "employee_id": employee_id,
        "employee_name": employees[employee_id]["name"],
        "leave_balance": leave_balance.get(employee_id, 0),
        "total_requests": len(emp_requests),
        "pending_requests": len([r for r in emp_requests if r["status"] == "Pending"]),
        "approved_requests": len([r for r in emp_requests if r["status"] == "Approved"]),
        "days_used_this_period": 20 - leave_balance.get(employee_id, 0)
    }

@mcp.tool()
def view_all_requests(status: str = "All") -> List[dict]:
    """
    View all leave requests, optionally filtered by status.
    Status options: All, Pending, Approved, Rejected
    """
    if status.lower() == "all":
        return leave_requests
    else:
        return [req for req in leave_requests if req["status"].lower() == status.lower()]

@mcp.tool()
def view_my_requests(employee_id: str) -> List[dict]:
    """View all leave requests for a specific employee"""
    return [req for req in leave_requests if req["employee_id"] == employee_id]

# ========== ADMIN TOOLS ==========

@mcp.tool()
def add_leave_balance(employee_id: str, days: int) -> dict:
    """Add leave days to an employee's balance (admin function)"""
    if employee_id not in employees:
        return {"error": f"Employee {employee_id} not found"}
    
    leave_balance[employee_id] = leave_balance.get(employee_id, 0) + days
    
    return {
        "message": f"✅ Added {days} days to balance",
        "employee": employees[employee_id]["name"],
        "old_balance": leave_balance[employee_id] - days,
        "new_balance": leave_balance[employee_id]
    }

@mcp.tool()
def department_summary(department: str = "All") -> dict:
    """Get leave statistics summary by department"""
    result = {
        "department": department,
        "total_employees": 0,
        "total_leave_balance": 0,
        "pending_requests": 0,
        "approved_requests": 0,
        "rejected_requests": 0
    }
    
    for emp_id, emp in employees.items():
        if department.lower() == "all" or emp["department"].lower() == department.lower():
            result["total_employees"] += 1
            result["total_leave_balance"] += leave_balance.get(emp_id, 0)
    
    # Count requests
    if department.lower() == "all":
        filtered_requests = leave_requests
    else:
        filtered_requests = [
            r for r in leave_requests 
            if employees.get(r["employee_id"], {}).get("department", "").lower() == department.lower()
        ]
    
    result["pending_requests"] = len([r for r in filtered_requests if r["status"] == "Pending"])
    result["approved_requests"] = len([r for r in filtered_requests if r["status"] == "Approved"])
    result["rejected_requests"] = len([r for r in filtered_requests if r["status"] == "Rejected"])
    result["total_requests"] = len(filtered_requests)
    
    return result

@mcp.tool()
def system_stats() -> dict:
    """Get overall system statistics"""
    return {
        "total_employees": len(employees),
        "total_leave_requests": len(leave_requests),
        "pending_requests": len([r for r in leave_requests if r["status"] == "Pending"]),
        "approved_requests": len([r for r in leave_requests if r["status"] == "Approved"]),
        "rejected_requests": len([r for r in leave_requests if r["status"] == "Rejected"]),
        "total_policies": len(knowledge_base),
        "departments": list(set(emp["department"] for emp in employees.values())),
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# ========== RESOURCES ==========

@mcp.resource("system://info")
def system_info() -> dict:
    """System information resource"""
    return {
        "name": "Leave Management System with RAG",
        "version": "2.0.0",
        "features": [
            "Employee Management",
            "Leave Request Processing",
            "RAG-Powered Policy Q&A",
            "Document Search",
            "Department Analytics"
        ],
        "stats": system_stats()
    }

@mcp.resource("help://quick-start")
def quick_start_guide() -> dict:
    """Quick start guide for using the system"""
    return {
        "title": "Leave Management System - Quick Start",
        "steps": [
            "1. Register employees with register_employee()",
            "2. Add policy documents with add_policy_document()",
            "3. Submit leave requests with request_leave()",
            "4. Ask policy questions with ask_policy_question()",
            "5. Approve/reject requests with approve_leave() or reject_leave()",
            "6. Check balances with check_balance()"
        ],
        "example_policy_question": "How many sick days am I entitled to?",
        "example_search": "search_policies('annual leave entitlement')"
    }

# ========== DEMO DATA SETUP ==========

def setup_demo_data():
    """Initialize system with demo data"""
    
    # Add employees
    register_employee("EMP001", "Alice Johnson", "alice@company.com", "Engineering")
    register_employee("EMP002", "Bob Smith", "bob@company.com", "HR")
    register_employee("EMP003", "Carol Davis", "carol@company.com", "Sales")
    register_employee("EMP004", "David Wilson", "david@company.com", "Engineering")
    
    # Add policy documents
    add_policy_document(
        "POL001",
        "Annual Leave Policy",
        """All full-time employees are entitled to 20 days of annual leave per calendar year. 
        Leave must be requested at least 2 weeks in advance for periods longer than 5 days. 
        Annual leave can be carried over up to 5 days to the next year. 
        Leave balance is prorated for new employees based on their start date.""",
        "Annual"
    )
    
    add_policy_document(
        "POL002",
        "Sick Leave Policy",
        """Employees are entitled to 10 days of paid sick leave per year. 
        Medical certificate is required for sick leave exceeding 3 consecutive days. 
        Sick leave cannot be carried over to the next year. 
        Unused sick leave does not get paid out upon termination.""",
        "Sick"
    )
    
    add_policy_document(
        "POL003",
        "Emergency Leave Policy",
        """Emergency leave is granted for unforeseen circumstances such as family emergencies. 
        Employees can take up to 3 days of emergency leave per incident. 
        Emergency leave is subject to manager approval and requires documentation. 
        This leave is deducted from annual leave balance.""",
        "Emergency"
    )
    
    add_policy_document(
        "POL004",
        "Remote Work Policy",
        """Employees may request remote work arrangements with manager approval. 
        Remote work is available up to 2 days per week for eligible roles. 
        Equipment and internet expenses may be reimbursed as per company guidelines. 
        Core working hours (10 AM - 3 PM) must be maintained regardless of location.""",
        "Remote"
    )
    
    # Add some leave requests
    request_leave("EMP001", "2024-12-23", "2024-12-27", "Annual", "Christmas holiday")
    request_leave("EMP002", "2024-12-30", "2025-01-03", "Annual", "New Year break")
    request_leave("EMP003", "2024-12-20", "2024-12-20", "Sick", "Medical appointment")
    
    # Approve one request
    if leave_requests:
        approve_leave(leave_requests[0]["request_id"], "ADMIN")

# ========== MAIN ENTRY POINT ==========

if __name__ == "__main__":
    # Setup demo data
    setup_demo_data()
    
    print("=" * 70)
    print("🏢 LEAVE MANAGEMENT SYSTEM WITH RAG")
    print("=" * 70)
    print(f"\n📊 SYSTEM STATUS:")
    print(f"   • Employees: {len(employees)}")
    print(f"   • Leave Requests: {len(leave_requests)}")
    print(f"   • Policy Documents: {len(knowledge_base)}")
    
    print(f"\n👥 DEMO EMPLOYEES:")
    for emp_id, emp in employees.items():
        balance = leave_balance.get(emp_id, 0)
        print(f"   • {emp['name']} ({emp_id}) - {emp['department']}: {balance} days")
    
    print(f"\n📋 LEAVE REQUESTS:")
    for req in leave_requests:
        print(f"   • {req['request_id']}: {req['employee_name']} - {req['status']}")
    
    print(f"\n📚 KNOWLEDGE BASE:")
    for pol_id, pol in knowledge_base.items():
        print(f"   • {pol_id}: {pol['title']} ({pol['category']})")
    
    print(f"\n🔧 AVAILABLE TOOLS:")
    print("   Employee Management:")
    print("      - register_employee()")
    print("      - view_employee()")
    print("      - list_all_employees()")
    
    print("   Leave Management:")
    print("      - request_leave()")
    print("      - approve_leave()")
    print("      - reject_leave()")
    print("      - check_balance()")
    print("      - view_all_requests()")
    
    print("   RAG / Knowledge Base:")
    print("      - add_policy_document()")
    print("      - search_policies()")
    print("      - ask_policy_question() ⭐")
    print("      - list_all_policies()")
    
    print("   Admin:")
    print("      - department_summary()")
    print("      - system_stats()")
    
    print(f"\n🚀 Starting FastMCP Server...")
    print("=" * 70)
    
    # Run the server
    mcp.run()
