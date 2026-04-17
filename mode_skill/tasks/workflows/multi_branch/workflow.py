"""Workflow definition for multi_branch.

Format:
  - "task1,task2,task3" means linear chain (task2 depends on task1, task3 depends on task2)
  - "task:dep1,dep2,dep3" means task depends on multiple deps
"""
WORKFLOW = "fetch,clean;fetch,analyze;fetch,export;save:clean,analyze,export"
