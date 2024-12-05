from datetime import datetime
from typing import List, Optional

from constants import CallStatus
from dataclasses import dataclass


@dataclass
class Company:
    id: str
    name: str
    phone_number: str
    max_concurrent_calls: int

@dataclass
class CallRecord:
    id: str
    company: Company
    status: CallStatus
    scheduled_time: datetime
    outbound_phone: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attempt_count: int = 0
    max_attempts: int = 3


