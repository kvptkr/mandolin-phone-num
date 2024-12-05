import asyncio
from datetime import datetime, timedelta

from controller import CallManager
from models import Company


async def main():
    print("\n" + "=" * 80)
    print("AUTOMATED CALL SYSTEM DEMONSTRATION".center(80))
    print("=" * 80 + "\n")

    # Create a limited pool of phone numbers to test resource constraints
    outbound_phones = [
        "1111111111",
        "2222222222"  # Only 2 phones to demonstrate resource limits
    ]

    print("📱 Available Phone Numbers:")
    for phone in outbound_phones:
        print(f"   • {phone}")
    print("\n" + "-" * 80 + "\n")

    call_manager = CallManager(outbound_phones)

    # Test Scenario 1: Basic Concurrent Calls
    print("\n🔹 SCENARIO 1: BASIC CONCURRENT CALLS")
    print("Testing normal operation with calls within company limits")
    print("-" * 80)

    company_a = Company(
        id="COMP1",
        name="Insurance Co A",
        phone_number="9999999999",
        max_concurrent_calls=2
    )

    print(f"Company: {company_a.name}")
    print(f"Max Concurrent Calls: {company_a.max_concurrent_calls}")
    print("\nAttempting to make 2 concurrent calls (should succeed)...")

    tasks = []
    for i in range(2):
        print(f"\nScheduling call {i + 1}...")
        call_id = await call_manager.schedule_call(
            company_a,
            datetime.now() + timedelta(minutes=1)
        )
        if call_id:
            print(f"✅ Call scheduled: {call_id}")
            tasks.append(call_manager.execute_call(call_id))
        else:
            print(f"❌ Failed to schedule call")

    await asyncio.gather(*tasks)
    print(f"\nFinal Status for {company_a.name}:")
    print(f"Active Calls: {call_manager.get_active_calls(company_a.id)}/{company_a.max_concurrent_calls}")
    for call in call_manager.get_company_call_history(company_a.id):
        print(f"• Call {call.id}:")
        print(f"  - Status: {call.status.value}")
        print(f"  - Using Phone: {call.outbound_phone}")
        print(f"  - Attempts: {call.attempt_count}")

    # Test Scenario 2: Exceeding Company Concurrent Call Limit
    print("\n" + "=" * 80)
    print("\n🔹 SCENARIO 2: EXCEEDING COMPANY CALL LIMIT")
    print("Attempting to exceed company's maximum concurrent call limit")
    print("-" * 80)

    company_b = Company(
        id="COMP2",
        name="Insurance Co B",
        phone_number="8888888888",
        max_concurrent_calls=1
    )

    print(f"Company: {company_b.name}")
    print(f"Max Concurrent Calls: {company_b.max_concurrent_calls}")
    print("\nAttempting to make 3 calls (should only allow 1)...")

    tasks = []
    for i in range(3):
        print(f"\nAttempting call {i + 1}...")
        call_id = await call_manager.schedule_call(
            company_b,
            datetime.now() + timedelta(minutes=1)
        )
        if call_id:
            print(f"✅ Call scheduled: {call_id}")
            tasks.append(call_manager.execute_call(call_id))
        else:
            print(f"❌ Call rejected (exceeds company limit)")

    await asyncio.gather(*tasks)
    print(f"\nFinal Status for {company_b.name}:")
    print(f"Active Calls: {call_manager.get_active_calls(company_b.id)}/{company_b.max_concurrent_calls}")

    # Test Scenario 3: Phone Number Pool Exhaustion
    print("\n" + "=" * 80)
    print("\n🔹 SCENARIO 3: PHONE NUMBER POOL EXHAUSTION")
    print("Testing behavior when all phone numbers are in use")
    print("-" * 80)

    company_c = Company(
        id="COMP3",
        name="Insurance Co C",
        phone_number="7777777777",
        max_concurrent_calls=5
    )

    print(f"Company: {company_c.name}")
    print(f"Available Phones: {len(outbound_phones)}")
    print(f"Attempting Calls: 4")
    print("\nAttempting to make more calls than available phones...")

    tasks = []
    for i in range(4):
        print(f"\nAttempting call {i + 1}...")
        call_id = await call_manager.schedule_call(
            company_c,
            datetime.now() + timedelta(minutes=1)
        )
        if call_id:
            print(f"✅ Call scheduled: {call_id}")
            tasks.append(call_manager.execute_call(call_id))
        else:
            print(f"❌ Call rejected (no available phones)")

    await asyncio.gather(*tasks)
    print(f"\nFinal Status for {company_c.name}:")
    print(f"Active Calls: {call_manager.get_active_calls(company_c.id)}")
    for call in call_manager.get_company_call_history(company_c.id):
        print(f"• Call {call.id}:")
        print(f"  - Status: {call.status.value}")
        print(f"  - Using Phone: {call.outbound_phone}")

    # Test Scenario 4: Failed Calls and Retries
    print("\n" + "=" * 80)
    print("\n🔹 SCENARIO 4: FAILED CALLS AND RETRIES")
    print("Testing retry mechanism for failed calls")
    print("-" * 80)

    company_d = Company(
        id="COMP4",
        name="Insurance Co D",
        phone_number="6666666666",
        max_concurrent_calls=1
    )

    print(f"Company: {company_d.name}")
    print("Making a call that will likely fail and retry...")

    call_id = await call_manager.schedule_call(
        company_d,
        datetime.now()
    )
    if call_id:
        print(f"✅ Call scheduled: {call_id}")
        await call_manager.execute_call(call_id)
        call_record = call_manager.call_records[call_id]
        print(f"\nCall Details:")
        print(f"• Status: {call_record.status.value}")
        print(f"• Attempt Count: {call_record.attempt_count}")

    # Test Scenario 5: Multiple Companies Competing
    print("\n" + "=" * 80)
    print("\n🔹 SCENARIO 5: RESOURCE COMPETITION")
    print("Multiple companies competing for limited phone numbers")
    print("-" * 80)

    companies = [
        Company(id=f"COMP{i}",
                name=f"Insurance Co {chr(ord('E') + i)}",  # E, F, G
                phone_number=f"555555555{i}",
                max_concurrent_calls=1)
        for i in range(3)
    ]

    print("Companies Competing:")
    for company in companies:
        print(f"• {company.name} (max calls: {company.max_concurrent_calls})")

    print("\nAttempting simultaneous calls from all companies...")

    tasks = []
    for company in companies:
        call_id = await call_manager.schedule_call(
            company,
            datetime.now()
        )
        if call_id:
            print(f"✅ Call scheduled for {company.name}: {call_id}")
            tasks.append(call_manager.execute_call(call_id))
        else:
            print(f"❌ Call rejected for {company.name}")

    await asyncio.gather(*tasks)

    print("\nFinal Status for All Companies:")
    print("-" * 40)
    for company in companies:
        print(f"\n{company.name}:")
        print(f"Active Calls: {call_manager.get_active_calls(company.id)}/{company.max_concurrent_calls}")
        for call in call_manager.get_company_call_history(company.id):
            print(f"• Call {call.id}:")
            print(f"  - Status: {call.status.value}")
            print(f"  - Using Phone: {call.outbound_phone}")
            print(f"  - Attempts: {call.attempt_count}")


if __name__ == "__main__":
    asyncio.run(main())