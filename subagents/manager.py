#!/usr/bin/env python3
"""
SubAgent Manager - Orchestrate, assign tasks, and manage multiple worker agents
Central command hub for scaling operations
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Dict, List

class AgentType(Enum):
    RESEARCH = "research"
    DATA_COLLECTOR = "data_collector"
    TRADER = "trader"
    CONTENT_CREATOR = "content_creator"
    MONITOR = "monitor"

class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class SubAgent:
    def __init__(self, name: str, agent_type: AgentType, cost_per_task: float, platform="fiverr"):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.agent_type = agent_type
        self.cost_per_task = cost_per_task
        self.platform = platform  # fiverr, upwork, telegram, etc
        self.status = "idle"
        self.tasks_completed = 0
        self.total_earned = 0.0
        self.created_at = datetime.utcnow().isoformat()
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.agent_type.value,
            "cost_per_task": self.cost_per_task,
            "platform": self.platform,
            "status": self.status,
            "tasks_completed": self.tasks_completed,
            "total_earned": self.total_earned,
            "created_at": self.created_at
        }

class Task:
    def __init__(self, description: str, task_type: str, priority: int = 5, deadline=None):
        self.id = str(uuid.uuid4())[:8]
        self.description = description
        self.type = task_type
        self.priority = priority  # 1-10, higher = more urgent
        self.status = TaskStatus.PENDING.value
        self.assigned_to = None
        self.deadline = deadline
        self.created_at = datetime.utcnow().isoformat()
        self.result = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "type": self.type,
            "priority": self.priority,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "deadline": self.deadline,
            "created_at": self.created_at,
            "result": self.result
        }

class SubAgentManager:
    def __init__(self, data_dir="C:/Users/firas/.openclaw/workspace/subagents"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.agents: Dict[str, SubAgent] = {}
        self.tasks: Dict[str, Task] = {}
        self.budget = 0.0  # Total budget available for agents
        
        self.load_state()
    
    def load_state(self):
        """Load agents and tasks from disk"""
        agents_file = self.data_dir / "agents.json"
        tasks_file = self.data_dir / "tasks.json"
        
        if agents_file.exists():
            with open(agents_file) as f:
                for agent_dict in json.load(f):
                    agent = SubAgent(
                        agent_dict["name"],
                        AgentType[agent_dict["type"].upper()],
                        agent_dict["cost_per_task"],
                        agent_dict["platform"]
                    )
                    agent.id = agent_dict["id"]
                    agent.status = agent_dict["status"]
                    agent.tasks_completed = agent_dict["tasks_completed"]
                    agent.total_earned = agent_dict["total_earned"]
                    self.agents[agent.id] = agent
        
        if tasks_file.exists():
            with open(tasks_file) as f:
                for task_dict in json.load(f):
                    task = Task(
                        task_dict["description"],
                        task_dict["type"],
                        task_dict.get("priority", 5),
                        task_dict.get("deadline")
                    )
                    task.id = task_dict["id"]
                    task.status = task_dict["status"]
                    task.assigned_to = task_dict.get("assigned_to")
                    task.result = task_dict.get("result")
                    self.tasks[task.id] = task
    
    def save_state(self):
        """Save agents and tasks to disk"""
        agents_file = self.data_dir / "agents.json"
        tasks_file = self.data_dir / "tasks.json"
        
        with open(agents_file, 'w') as f:
            json.dump([a.to_dict() for a in self.agents.values()], f, indent=2)
        
        with open(tasks_file, 'w') as f:
            json.dump([t.to_dict() for t in self.tasks.values()], f, indent=2)
    
    def hire_agent(self, name: str, agent_type: AgentType, cost_per_task: float, platform="fiverr") -> SubAgent:
        """Hire a new sub-agent"""
        agent = SubAgent(name, agent_type, cost_per_task, platform)
        self.agents[agent.id] = agent
        self.save_state()
        return agent
    
    def create_task(self, description: str, task_type: str, priority: int = 5) -> Task:
        """Create a new task"""
        task = Task(description, task_type, priority)
        self.tasks[task.id] = task
        self.save_state()
        return task
    
    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """Assign a task to an agent"""
        if task_id not in self.tasks or agent_id not in self.agents:
            return False
        
        task = self.tasks[task_id]
        agent = self.agents[agent_id]
        
        task.status = TaskStatus.ASSIGNED.value
        task.assigned_to = agent_id
        agent.status = "busy"
        
        self.save_state()
        return True
    
    def complete_task(self, task_id: str, result: str = None) -> bool:
        """Mark task as complete"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        agent = self.agents.get(task.assigned_to)
        
        task.status = TaskStatus.COMPLETED.value
        task.result = result
        
        if agent:
            agent.tasks_completed += 1
            agent.total_earned += agent.cost_per_task
            agent.status = "idle"
        
        self.save_state()
        return True
    
    def get_report(self) -> Dict:
        """Generate operational report"""
        pending_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.PENDING.value]
        assigned_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.ASSIGNED.value]
        completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED.value]
        
        total_cost = sum(a.total_earned for a in self.agents.values())
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {
                "total": len(self.agents),
                "active": sum(1 for a in self.agents.values() if a.status == "busy"),
                "idle": sum(1 for a in self.agents.values() if a.status == "idle")
            },
            "tasks": {
                "pending": len(pending_tasks),
                "assigned": len(assigned_tasks),
                "completed": len(completed_tasks),
                "total": len(self.tasks)
            },
            "finances": {
                "total_spent": total_cost,
                "agents_by_earnings": sorted(
                    [(a.name, a.total_earned) for a in self.agents.values()],
                    key=lambda x: x[1],
                    reverse=True
                )
            }
        }

def main():
    print("=" * 70)
    print("Sub-Agent Manager - Orchestration System")
    print("=" * 70)
    
    manager = SubAgentManager()
    
    # Example: Hire agents
    print("\n[1] Hiring sub-agents...")
    
    researcher = manager.hire_agent(
        "Data Analyst",
        AgentType.DATA_COLLECTOR,
        cost_per_task=7.50,
        platform="fiverr"
    )
    print(f"  [OK] Hired: {researcher.name} (ID: {researcher.id})")
    
    content_creator = manager.hire_agent(
        "Twitter Content Creator",
        AgentType.CONTENT_CREATOR,
        cost_per_task=15.0,
        platform="fiverr"
    )
    print(f"  [OK] Hired: {content_creator.name} (ID: {content_creator.id})")
    
    # Create tasks
    print("\n[2] Creating tasks...")
    
    task1 = manager.create_task(
        "Monitor Aave liquidation events for past 24h, compile report",
        task_type="research",
        priority=9
    )
    print(f"  [OK] Task created: {task1.description[:40]}... (ID: {task1.id})")
    
    task2 = manager.create_task(
        "Write 3 daily Twitter threads about crypto market trends",
        task_type="content",
        priority=7
    )
    print(f"  [OK] Task created: {task2.description[:40]}... (ID: {task2.id})")
    
    # Assign tasks
    print("\n[3] Assigning tasks...")
    manager.assign_task(task1.id, researcher.id)
    manager.assign_task(task2.id, content_creator.id)
    print(f"  [OK] Task {task1.id} assigned to {researcher.name}")
    print(f"  [OK] Task {task2.id} assigned to {content_creator.name}")
    
    # Simulate task completion
    print("\n[4] Tasks completing...")
    manager.complete_task(task1.id, "Report: 3 liquidations detected")
    manager.complete_task(task2.id, "Twitter threads posted, 1.2k impressions")
    print(f"  [OK] Tasks marked complete")
    
    # Report
    print("\n[5] Operational Report")
    report = manager.get_report()
    print(f"\nAgents:")
    print(f"  Total: {report['agents']['total']}")
    print(f"  Active: {report['agents']['active']}")
    print(f"  Idle: {report['agents']['idle']}")
    
    print(f"\nTasks:")
    print(f"  Pending: {report['tasks']['pending']}")
    print(f"  Assigned: {report['tasks']['assigned']}")
    print(f"  Completed: {report['tasks']['completed']}")
    
    print(f"\nFinances:")
    print(f"  Total Spent: ${report['finances']['total_spent']:.2f}")
    for agent_name, earnings in report['finances']['agents_by_earnings']:
        print(f"    {agent_name}: ${earnings:.2f}")
    
    # Save report
    report_path = Path("C:/Users/firas/.openclaw/workspace/reports/subagent-report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n[OK] Report saved: {report_path}")

if __name__ == '__main__':
    main()
