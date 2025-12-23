from ipaddress import IPv4Network
from typing import Tuple, List, Dict, Any


def check_cidr(cidr: IPv4Network, start_prefix: int) -> IPv4Network:
    """Adjust network prefix if start prefix is smaller than network prefix.

    Args:
        cidr: IPv4 network to check
        start_prefix: Desired starting prefix length

    Returns:
        IPv4Network with adjusted prefix if needed, otherwise original

    Example:
        >>> net = IPv4Network("192.168.1.0/24")
        >>> check_cidr(net, 23)
        IPv4Network('192.168.0.0/23')
    """
    if start_prefix < cidr.prefixlen:
        return IPv4Network(f"{cidr.network_address}/{start_prefix}", strict=False)
    return cidr


def build_display_list(
    cidr: IPv4Network, start_prefix: int, end_prefix: int
) -> Tuple[List[List[Dict[str, Any]]], List[Tuple[int, int, int]]]:
    """Build subnet visualization grid with span information.

    Creates a 2D grid where columns represent prefix lengths and rows
    represent individual subnets. Larger subnets span multiple rows.

    Args:
        cidr: Base IPv4 network to subdivide
        start_prefix: Starting prefix length (smaller = larger subnets)
        end_prefix: Ending prefix length (larger = smaller subnets)

    Returns:
        Tuple of (data, spans) where:
            - data: 2D list of subnet dictionaries
            - spans: List of (row, col, span_size) tuples for merged cells

    Raises:
        ValueError: If prefix ranges are invalid

    Example:
        >>> net = IPv4Network("192.168.1.0/24")
        >>> data, spans = build_display_list(net, 24, 26)
        >>> len(data)  # rows
        4
        >>> len(data[0])  # columns
        3
    """
    # Validate inputs
    if start_prefix < 0 or end_prefix > 32:
        raise ValueError("Prefix must be between 0 and 32 for IPv4")
    if start_prefix > end_prefix:
        raise ValueError(
            f"start_prefix ({start_prefix}) must be <= " f"end_prefix ({end_prefix})"
        )

    cidr = check_cidr(cidr, start_prefix)
    column_count = end_prefix - start_prefix + 1
    row_count = 2 ** (end_prefix - cidr.prefixlen)

    # Pre-allocate grid
    data: List[List[Dict[str, Any]]] = [
        [{} for _ in range(column_count)] for _ in range(row_count)
    ]
    spans: List[Tuple[int, int, int]] = []

    # Build columns (each represents a prefix length)
    for col_num, prefix in enumerate(range(start_prefix, end_prefix + 1)):
        span_size = 2 ** (end_prefix - prefix)
        row_num = 0

        # Use generator to save memory - don't convert to list
        for net in cidr.subnets(new_prefix=prefix):
            data[row_num][col_num] = {
                "network": net.with_prefixlen,
                "spansize": span_size,
            }

            # Track spans > 1 for table cell merging
            if span_size > 1:
                spans.append((row_num, col_num, span_size))

            row_num += span_size

    return data, spans


def validate_network_range(
    cidr: IPv4Network, start_prefix: int, end_prefix: int
) -> Tuple[bool, str]:
    """Validate if network range is reasonable for display.

    Args:
        cidr: Network to validate
        start_prefix: Start prefix
        end_prefix: End prefix

    Returns:
        Tuple of (is_valid, message)
    """
    try:
        if start_prefix < 0 or end_prefix > 32:
            return False, "Prefix must be between 0 and 32"
        if start_prefix > end_prefix:
            return False, "Start prefix must be <= end prefix"

        # Check if result would be too large
        adjusted = check_cidr(cidr, start_prefix)
        row_count = 2 ** (end_prefix - adjusted.prefixlen)
        col_count = end_prefix - start_prefix + 1
        total_cells = row_count * col_count

        if total_cells > 10000:  # Arbitrary limit
            return False, (
                f"Result would be too large ({row_count} rows × "
                f"{col_count} cols = {total_cells:,} cells). "
                f"Consider smaller range."
            )

        return True, "Valid"
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    # Test with validation
    network = IPv4Network("192.168.1.0/24")
    start = 23
    end = 26

    valid, msg = validate_network_range(network, start, end)
    if not valid:
        print(f"Error: {msg}")
    else:
        data, spans = build_display_list(network, start, end)
        print(f"Generated grid: {len(data)} rows × {len(data[0])} columns")
        print(f"Spans: {len(spans)}")

        # Display sample
        print("\nSample subnets:")
        for row in range(min(4, len(data))):
            for col in range(len(data[0])):
                if net_info := data[row][col]:
                    print(f"  [{row},{col}]: {net_info}")
