"""
@author Huy Le (huyisme-005)
backend/celeryconfig.py

Celery configuration settings for broker and result backend.
"""

broker_url = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/0"
