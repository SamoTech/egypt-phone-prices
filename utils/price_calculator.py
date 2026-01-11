def compute_metrics_for_row(row, store_columns):
    prices = []
    for col in store_columns:
        val = (row.get(col) or "").strip()
        if not val:
            continue
        try:
            price = float(val)
            if price > 0:
                prices.append(price)
        except ValueError:
            continue

    row["availability_score"] = str(len(prices))

    if not prices:
        row["lowest_price"] = ""
        row["highest_price"] = ""
        row["average_price"] = ""
        row["price_variance"] = ""
        row["best_store"] = ""
        return

    low = min(prices)
    high = max(prices)
    avg = sum(prices) / len(prices)
    var = high - low

    row["lowest_price"] = f"{low:.0f}"
    row["highest_price"] = f"{high:.0f}"
    row["average_price"] = f"{avg:.0f}"
    row["price_variance"] = f"{var:.0f}"

    for col in store_columns:
        val = (row.get(col) or "").strip()
        try:
            if float(val) == low:
                row["best_store"] = col
                break
        except Exception:
            continue
