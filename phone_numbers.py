import asyncio
from typing import List, Set, Optional


class PhoneNumberPool:
    def __init__(self, phone_numbers: List[str]):
        self.available_phones: Set[str] = set(phone_numbers)
        self.in_use_phones: Set[str] = set()
        self.lock = asyncio.Lock()

    async def acquire_phone(self) -> Optional[str]:
        async with self.lock:
            if not self.available_phones:
                return None
            phone = self.available_phones.pop()
            self.in_use_phones.add(phone)
            return phone

    async def release_phone(self, phone: str):
        async with self.lock:
            if phone in self.in_use_phones:
                self.in_use_phones.remove(phone)
                self.available_phones.add(phone)