import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional

from constants import CallStatus
from models import CallRecord, Company
from phone_numbers import PhoneNumberPool


class CompanyCallTracker:
    def __init__(self):
        self.active_calls: Dict[str, int] = defaultdict(int)
        self.lock = asyncio.Lock()

    async def can_make_call(self, company: Company) -> bool:
        """
        Check if a company has additional capacity to make calls

        """
        async with self.lock:
            return self.active_calls[company.id] < company.max_concurrent_calls

    async def increment_active_calls(self, company: Company) -> bool:
        async with self.lock:
            if self.active_calls[company.id] < company.max_concurrent_calls:
                self.active_calls[company.id] += 1
                return True
            return False

    async def decrement_active_calls(self, company: Company):
        async with self.lock:
            if self.active_calls[company.id] > 0:
                self.active_calls[company.id] -= 1
    def get_company_calls(self, company_id: str) -> int:
        return self.active_calls[company_id]

class CallManager:
    def __init__(self, phone_numbers: List[str]):
        self.phone_pool = PhoneNumberPool(phone_numbers)
        self.company_tracker = CompanyCallTracker()
        self.call_records: Dict[str, CallRecord] = {}
        self.call_history: Dict[str, List[CallRecord]] = defaultdict(list)

    async def _handle_failed_call(self, call_id: str) -> None:
            call_record = self.call_records[call_id]
            if call_record.attempt_count < call_record.max_attempts:
                await self._reschedule_call(call_id)
            else:
                call_record.notes = "Max retry attempts reached"

    async def _reschedule_call(self, call_id: str) -> None:
        call_record = self.call_records[call_id]
        delay = 2 ** call_record.attempt_count  # Exponential backoff
        new_time = datetime.now() + timedelta(minutes=delay)
        call_record.scheduled_time = new_time
        call_record.status = CallStatus.SCHEDULED


    async def schedule_call(self, company: Company, scheduled_time: datetime) -> Optional[str]:
        if not await self.company_tracker.can_make_call(company):
            return None

        call_id = f"CALL_{company.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        call_record = CallRecord(
            id=call_id,
            company=company,
            status=CallStatus.SCHEDULED,
            scheduled_time=scheduled_time,
            outbound_phone=''
        )
        self.call_records[call_id] = call_record

        return call_id

    async def _simulate_phone_call(self, call_record: CallRecord) -> None:
        """
        Simulate a phone call with deterministic outcomes based on rules:
        - First attempt: BUSY for companies with ID ending in 1
        - Second attempt: NO_ANSWER for companies with ID ending in 2
        - Third attempt: FAILED for companies with ID ending in 3
        - All attempts for companies with ID ending in 4: FAILED
        - All other cases: SUCCESS
        """
        # Simulate call duration
        await asyncio.sleep(1)  # Fixed duration for predictability

        company_id = call_record.company.id
        attempt = call_record.attempt_count

        # Determine call outcome based on company ID and attempt number
        if company_id.endswith('4'):
            # Companies ending in 4 always fail
            call_record.status = CallStatus.FAILED
        elif company_id.endswith('1') and attempt == 1:
            # First attempt for companies ending in 1 is busy
            call_record.status = CallStatus.BUSY
        elif company_id.endswith('2') and attempt == 2:
            # Second attempt for companies ending in 2 gets no answer
            call_record.status = CallStatus.NO_ANSWER
        elif company_id.endswith('3') and attempt == 3:
            # Third attempt for companies ending in 3 fails
            call_record.status = CallStatus.FAILED
        else:
            # All other cases succeed
            call_record.status = CallStatus.SUCCESS

    async def execute_call(self, call_id: str) -> None:
        """
        1. get the call record
        2. Ensure that we're not maxxing out the number of calls at any given time for a specific company
        2. acquire phone, if none available, then we want to reschedule
        3. keep track of call status in a tracker
        4. if the call failed, then we want to retry
        5. Lastly, we clean up and make su
        :param self:
        :param call_id:
        :return:
        """
        call_record = self.call_records[call_id]

        if not await self.company_tracker.increment_active_calls(call_record.company):
            await self._reschedule_call(call_id)
            return

        outbound_phone = await self.phone_pool.acquire_phone()
        if not outbound_phone:
            await self.company_tracker.decrement_active_calls(call_record.company)
            await self._reschedule_call(call_id)
            return

        call_record.outbound_phone = outbound_phone

        try:
            call_record.status = CallStatus.IN_PROGRESS
            call_record.start_time = datetime.now()
            call_record.attempt_count += 1

            await self._simulate_phone_call(call_record)

            if call_record.status in [CallStatus.BUSY, CallStatus.NO_ANSWER, CallStatus.FAILED]:
                await self._handle_failed_call(call_id)

            call_record.end_time = datetime.now()
            self.call_history[call_record.company.id].append(call_record)

        except Exception as e:
            call_record.status = CallStatus.FAILED
            await self._handle_failed_call(call_id)
        finally:
            await self.phone_pool.release_phone(outbound_phone)
            await self.company_tracker.decrement_active_calls(call_record.company)

    def get_call_status(self, call_id: str) -> CallStatus:
        return self.call_records[call_id].status

    def get_company_call_history(self, company_id: str) -> List[CallRecord]:
        return self.call_history[company_id]

    def get_active_calls(self, company_id: str) -> int:
        return self.company_tracker.get_company_calls(company_id)


