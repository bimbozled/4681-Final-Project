from __future__ import annotations

from metrics import get_collector


def get_trace_id_info(trace_id: str) -> dict | None:
    """
    Fetch query information by trace ID.
    
    Returns:
        Dictionary with query metrics if found, None otherwise.
    """
    collector = get_collector()
    return collector.get_query_by_trace_id(trace_id)


def list_all_trace_ids() -> list[str]:
    """
    Get all stored trace IDs.
    
    Returns:
        List of trace ID strings.
    """
    collector = get_collector()
    return collector.get_all_trace_ids()


if __name__ == "__main__":
    print("Trace ID Utility - How to fetch trace IDs")
    print("=" * 50)
    
    all_ids = list_all_trace_ids()
    print(f"\nTotal trace IDs stored: {len(all_ids)}")
    
    if all_ids:
        print(f"\nAll trace IDs: {', '.join(all_ids)}")
        
        example_id = all_ids[-1]
        print(f"\nExample: Fetching details for trace ID '{example_id}'")
        print("-" * 50)
        
        query_info = get_trace_id_info(example_id)
        if query_info:
            print(f"Trace ID: {query_info['trace_id']}")
            print(f"Timestamp: {query_info['timestamp']}")
            print(f"Status: {query_info['status']}")
            print(f"User Query: {query_info['user_query']}")
            print(f"Latency: {query_info['total_latency_ms']}ms")
            print(f"Row Count: {query_info['row_count']}")
        else:
            print("Not found")
    else:
        print("\nNo trace IDs found. Run some queries first.")

