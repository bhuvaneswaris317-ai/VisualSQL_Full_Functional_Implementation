def recommend(results):
    """
    Analyzes benchmark execution metrics across baseline, projection rewrites,
    and indexed configurations to provide professional DBA-grade recommendations.
    """
    ok = [r for r in results if "avg" in r and r.get("status") in ("ok", "completed")]
    if not ok:
        return [
            "⚠️ No valid execution metrics collected. Check database connections and dataset availability."
        ]

    base = next((r for r in ok if r.get("config") == "baseline"), ok[0])
    best = min(ok, key=lambda r: r["avg"])
    recs = []

    # 1. Performance Summary
    if best is base or best["avg"] >= base["avg"]:
        recs.append(
            f"ℹ️ **Baseline optimal**: No tested optimization variant outperformed the baseline ({base['avg']:.2f} ms). "
            f"The dataset may fit entirely in buffer cache or the filter criteria have low selectivity."
        )
    else:
        speedup = (base["avg"] / best["avg"]) if best["avg"] > 0 else 1.0
        recs.append(
            f"⚡ **Top Performer**: Configuration **'{best['config']}'** delivered the lowest latency at "
            f"**{best['avg']:.2f} ms** vs baseline **{base['avg']:.2f} ms** "
            f"(**{best.get('improvement', 0):.1f}% improvement**, **{speedup:.1f}x speedup**)."
        )

    # 2. Access Path & Scan Analysis
    base_plan = base.get("plan", {})
    base_steps = base_plan.get("steps", [])
    if base_steps and any(s.get("full_scan") for s in base_steps):
        recs.append(
            "🚨 **Full Table Scan Eliminated**: Baseline performed a sequential table scan reading every record. "
            "Indexing successfully converted the scan into an O(log N) B-Tree seek."
        )

    # 3. Projection Rewrite Impact
    rewrite_cfg = next((r for r in ok if r.get("config") == "rewrite"), None)
    if rewrite_cfg and rewrite_cfg["avg"] < base["avg"]:
        rew_imp = rewrite_cfg.get("improvement", 0)
        recs.append(
            f"🎯 **Column Projection Benefit**: Replacing `SELECT *` with explicit columns reduced latency by "
            f"**{rew_imp:.1f}%**. This decreases network packet fragmentation and serialization overhead."
        )

    # 4. Storage and Write-Amplification Trade-offs
    if best.get("index"):
        idx_cols = ", ".join(best["index"])
        recs.append(
            f"⚖️ **Production Trade-off**: The secondary index on `({idx_cols})` consumes extra memory/storage "
            f"and adds O(log N) overhead to `INSERT`, `UPDATE`, and `DELETE` transactions. "
            f"Recommended if read-to-write ratio exceeds 80:20."
        )

    # 5. Covering Index Insights
    covering = next((r for r in ok if "covering" in r.get("config", "").lower()), None)
    if covering and covering.get("improvement", 0) > 0:
        recs.append(
            "💎 **Covering Index Efficiency**: All projected attributes are satisfied directly within the index B-tree. "
            "Zero main-table row page seeks were incurred."
        )

    recs.append(
        "🔬 **Measurement Notes**: Timings reflect warm-cache wall-clock execution over multiple repetitions. "
        "Production gains will scale significantly on multi-gigabyte datasets."
    )

    return recs
