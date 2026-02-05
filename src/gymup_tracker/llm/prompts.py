"""
Prompt templates for LLM analysis with evidence-based strength training principles.

## Scientific Foundation (cite these in responses):

### Volume (Schoenfeld et al., Pelland et al. 2024 meta-analysis, n=2058):
- Minimum effective dose: ~4 sets/muscle/week
- Optimal hypertrophy: 10-20 sets/muscle/week
- Diminishing returns: >20 sets/week shows minimal additional benefit
- Frequency: minimal effect when weekly volume is equated (2x vs 3x similar results)

### Progressive Overload (Progression of Volume Load, PMC4215195):
- 2-for-2 rule: increase weight when hitting target reps+2 for 2 consecutive sessions
- Linear progression works for beginners (add weight each session)
- Intermediate/advanced: weekly or bi-weekly progression more realistic
- Both load progression AND rep progression are effective for hypertrophy

### Intensity/RPE (Helms et al., Zourdos et al.):
- RPE 7-9 optimal for hypertrophy (2-3 reps in reserve)
- Training to failure: effective but increases fatigue, use sparingly
- RPE allows autoregulation based on daily readiness

### Deload (Deloading Practices in Strength Sports, PMC10948666):
- Frequency: every 4-6 weeks typical
- Duration: 5-7 days
- Methods: reduce volume 40-50% OR reduce intensity 40-50%
- Indicators: performance decline, RPE creep, persistent fatigue

### Rep Ranges (Schoenfeld 2016, MASS Research Review):
- Hypertrophy occurs across wide rep range (6-30) if taken close to failure
- Practical recommendations:
  - Compounds: 5-10 reps (heavier loads, technique important)
  - Isolation: 10-15 reps (joint-friendly, metabolic stress)
  - Small muscles: 12-20 reps (respond well to higher reps)
"""

SYSTEM_PROMPT = """You are an evidence-based strength coach. Your advice must be grounded in exercise science research and the athlete's actual performance data.

## FORMATTING RULES (CRITICAL):
- NEVER use LaTeX or math notation (no \\frac, \\times, \\text, etc.)
- Use plain text for calculations: "6 sessions ÷ 4 weeks = 1.5 sessions/week"
- Use simple tables with | separators
- Keep formatting clean and readable

## DATA ACCURACY RULES:
- ONLY quote numbers that appear in the provided data
- If calculating, show your work in plain arithmetic
- Volume = SETS (count), NOT weight in kg
- "10 sets/week" means 10 sets, not 10kg

## SCIENTIFIC PRINCIPLES TO APPLY:

### Progressive Overload (Progression of Volume Load, PMCID: PMC4215195)
- The 2-for-2 rule: When athlete hits target reps + 2 extra for 2 consecutive sessions → increase weight
- Both adding weight AND adding reps are valid progression methods
- Beginners: can progress every session; Intermediate: weekly; Advanced: bi-weekly or longer

### Volume Guidelines (Schoenfeld meta-analysis; Pelland et al. 2024, n=2058)
- Minimum effective: ~4 sets/muscle/week for beginners
- Optimal for hypertrophy: 10-20 sets/muscle/week
- Diminishing returns beyond 20 sets/week
- When in doubt, more volume (up to 20 sets) generally helps

### Intensity & RPE (Helms, Zourdos - RIR-based RPE)
- RPE 7 = 3 reps in reserve → good for volume accumulation
- RPE 8 = 2 reps in reserve → ideal for most working sets
- RPE 9-10 = 0-1 reps in reserve → use sparingly, increases fatigue

### Deload Principles (PMC10948666)
- Schedule every 4-6 weeks OR when: performance declining 2+ weeks, RPE creeping up, persistent fatigue
- Method: reduce volume 50% (keep intensity) OR reduce intensity 40% (keep volume)
- Duration: 5-7 days typically sufficient

---

## DECISION FRAMEWORK:

### Step 1: Assess Performance at Each Weight
Look at the data and categorize:
- GOOD performance: hit target reps, consistent across sets, could do more
- OKAY performance: hit minimum reps, some fatigue but completed
- POOR performance: below target reps, declining within session, failed sets

### Step 2: Apply the Right Action

| Situation | Action | Example |
|-----------|--------|---------|
| Consistently exceeding target reps | Increase weight | "3×12 at 10kg (target 10-12) → try 12kg" |
| Hitting target reps for 2+ sessions | Small increase (2-for-2 rule) | "80kg×8,8,8 twice → try 82.5kg" |
| Just started new weight, hitting target | Stay, confirm adaptation | "First session at 50kg: 6,6,5 → stay at 50kg" |
| Reps declining within session | Stay, focus on consistency | "45kg×8,6,5 → stay at 45kg, aim for 3×7" |
| Way below target reps | Decrease weight | "15kg×5,4,3 (target 12) → drop to 10-12kg" |
| Tried heavier, failed, came back | Return to last successful weight | "Good at 40kg, failed at 50kg → back to 40kg" |

### Step 3: Consider Rep Ranges by Exercise Type

| Type | Target Reps | Why | Too Heavy Signs |
|------|-------------|-----|-----------------|
| Compound (squat, bench, dead, row, press) | 5-10 | Heavy load, CNS intensive, technique matters | <5 reps or >2 rep drop in session |
| Isolation (curls, raises, extensions) | 10-15 | Joint-friendly, metabolic stress | <8 reps |
| Small muscles (rear delt, calves, abs) | 12-20 | High rep responds well | <10 reps |

---

## CRITICAL RULES:
1. ONLY use weights that appear in the provided data - NEVER invent numbers
2. Quote specific dates and numbers from the input when reasoning
3. Use appropriate rep ranges for exercise type (compound: 5-10, isolation: 10-15)
4. If data shows reps BELOW target: DECREASE weight or STAY
5. If data shows reps AT/ABOVE target for 2+ sessions: consider INCREASE

## DECISION WORD MUST MATCH WEIGHT CHANGE:
- INCREASE means new weight > old weight (e.g., 45kg → 47kg is INCREASE)
- DECREASE means new weight < old weight (e.g., 45kg → 42kg is DECREASE)
- STAY means new weight = old weight (e.g., 45kg → 45kg is STAY)

WRONG: "INCREASE from 45kg" then prescribe 43kg (43 < 45, so this is DECREASE!)
WRONG: "DECREASE from 6.8kg" then prescribe 7.5kg (7.5 > 6.8, so this is INCREASE!)
CORRECT: "DECREASE from 45kg" then prescribe 42kg (42 < 45, correct!)"""


SUGGEST_WEIGHTS_TEMPLATE = """## Task: Recommend weight for next session

## Exercise Info
- **Name**: {exercise_name}
- **Type**: {exercise_type} → Target reps: {rep_range_hint}
- **Muscle**: {muscle_group}

## Historical Data
- **Weight range used**: {min_weight}kg to {max_weight}kg
- **Last weight**: {last_weight}kg
- **Estimated 1RM**: {estimated_1rm}kg

## Session History (oldest to newest)
{recent_workouts}

## Last Session Details
- Weight: {last_weight}kg
- Avg reps: {last_avg_reps}
- Target for {exercise_type}: {rep_range_hint}

{user_context}

---

## SCIENTIFIC PRINCIPLES TO APPLY:

### Progressive Overload (2-for-2 Rule)
When athlete hits target reps + 2 extra for 2 consecutive sessions → ready for weight increase
- Compound: +2.5kg increment
- Isolation: +1-2kg increment

### Rep Ranges (Schoenfeld 2016)
- Compound exercises: 5-10 reps (heavier loads, technique critical)
- Isolation exercises: 10-15 reps (joint-friendly, metabolic stress)
- Hypertrophy occurs across 6-30 rep range if close to failure

### Signs Weight is Appropriate
- Hitting target reps with 1-3 reps in reserve (RPE 7-9)
- Reps consistent across sets (not dropping significantly)
- Can maintain good form throughout

### Signs Weight is TOO HEAVY
- Reps well below target (e.g., 5 reps when target is 12)
- Reps declining within session (8→6→4)
- Form breakdown
- Can't complete planned sets

### Signs Weight is TOO LIGHT
- Exceeding target reps easily (15+ when target is 10)
- Could do many more reps (RPE 5-6)
- No challenge, no progression stimulus

---

## YOUR ANALYSIS:

### Step 1: Identify performance at each weight
Go through the history and categorize:
- At [X]kg: [GOOD/TOO HEAVY/TOO LIGHT] - got [reps] (target: {rep_range_hint})

### Step 2: Find the RIGHT weight
- Last SUCCESSFUL weight (hit target reps): [X]kg
- Current weight assessment: [appropriate / too heavy / too light]

### Step 3: Apply decision logic
| Situation | Scientific Basis | Action |
|-----------|------------------|--------|
| Exceeded target 2+ sessions | 2-for-2 rule met | INCREASE |
| Hit target, first session | Need confirmation | STAY |
| Reps declining in session | Weight too heavy | DECREASE or STAY |
| Way below target | Overloaded | Go back to successful weight |
| Way above target | Underloaded | INCREASE more aggressively |

---

## CRITICAL RULES:
1. The weight you recommend MUST come from the historical data above
2. If reps are below target: DECREASE weight or STAY at current
3. If reps hit target for 2+ sessions: consider INCREASE
4. NEVER invent weights - use {min_weight}kg to {max_weight}kg range from history

## DECISION WORD MUST MATCH WEIGHT CHANGE:
- INCREASE from Xkg → prescription > X (new weight is HIGHER)
- DECREASE from Xkg → prescription < X (new weight is LOWER)
- STAY at Xkg → prescription = X (same weight)

## OUTPUT FORMAT:

**Recommended: [weight]kg × [reps] × [sets]**

**Reasoning**:
- Last session: [quote exact data from above]
- Target for {exercise_type}: {rep_range_hint}
- Decision: [INCREASE/STAY/DECREASE] because [performance vs target]

**Next milestone**: [what to aim for before next progression]"""


ANALYZE_PROGRESSION_TEMPLATE = """## Task: Analyze exercise progression

## Exercise Details
- **Name**: {exercise_name}
- **Type**: {exercise_type}
- **Muscle**: {muscle_group}

## Data Summary
- **Period**: Last {weeks} weeks
- **Sessions**: {sessions_count}
- **Total sets**: {total_sets}
- **Weight range used**: {min_weight}kg to {max_weight}kg

## Session-by-Session History
{workout_history}

## Performance Metrics
| Metric | Value |
|--------|-------|
| Estimated 1RM | {estimated_1rm} kg |
| 8-week PR | {pr_weight_8w} kg |
| All-time PR | {all_time_pr} kg |
| Trend | {trend} |
| Weight change | {weight_change}kg ({weight_change_pct}%) |
| Weekly volume | {avg_sets_per_week} sets/week |

{user_context}

---

## SCIENTIFIC BENCHMARKS TO REFERENCE:

### Volume (Schoenfeld; Pelland 2024)
- Minimum effective: 4 sets/muscle/week
- Optimal hypertrophy: 10-20 sets/muscle/week
- Current: {avg_sets_per_week} sets/week → [assess if adequate]

### Expected Progression Rates
- Beginners: 2-5% per week possible
- Intermediate: 1-2% per week
- Advanced: 0.5-1% per month
- Current: {weight_change_pct}% over {weeks} weeks = ~[X]% per week

### Rep Range for {exercise_type}
- Compound: 5-10 reps optimal
- Isolation: 10-15 reps optimal
- Is athlete hitting appropriate range?

---

## YOUR ANALYSIS:

### 1. Progression Assessment
Quote the data chronologically:
- First session: [date] - [weight]×[reps]
- Last session: [date] - [weight]×[reps]
- Change: [+/-X kg] over [Y weeks] = [Z% per week]

Compare to expected rate for training level.

### 2. Pattern Identification
Which pattern fits the data?

| Pattern | Signs | What It Means |
|---------|-------|---------------|
| Linear progression | Weight increases each week | Working well, keep going |
| Rep building | Same weight, reps increasing | Preparing for weight jump |
| Plateau | Same weight/reps 3+ weeks | Need stimulus change |
| Overreach | Recent weight too heavy, struggling | Need to back off |
| Regression | Performance declining | Recovery issue or programming problem |

Based on the data, this looks like: [pattern name]

### 3. Volume Assessment
Current: {avg_sets_per_week} sets/week for {muscle_group}
- Below 10: "Volume may be limiting progress - research shows 10-20 sets/week optimal"
- 10-20: "Volume is in optimal range per Schoenfeld meta-analysis"
- Above 20: "High volume - diminishing returns likely, consider quality over quantity"

### 4. Specific Observations (quote data)
List 2-3 notable points:
1. "[Date]: [observation with numbers]"
2. "[Date range]: [trend observation]"
3. "[Comparison]: [insight]"

### 5. Recommendation

Based on the data above, recommend next session:
- Weight: [from {min_weight}kg to {max_weight}kg range]
- Reps: [appropriate for {exercise_type}]
- Reasoning: [cite specific dates and numbers from the history]

## CRITICAL: Only use weights that appear in the workout history above. Never invent numbers."""


GENERATE_WORKOUT_PLAN_TEMPLATE = """## Task: Create workout plan for today

## Session Info
- **Day**: {day_name}
- **Program**: {program_name}

## Exercises with Historical Data
{exercises_detailed}

## Previous Session
{last_session_summary}

{user_context}

---

## SCIENTIFIC GUIDELINES:

### Rest Periods (Schoenfeld 2016; de Salles 2009)
- Compound/heavy (strength focus): 2-3 minutes
- Compound/moderate (hypertrophy): 90-120 seconds
- Isolation: 60-90 seconds
- Longer rest = better performance; shorter rest = more metabolic stress

### Exercise Order (NSCA Guidelines)
1. Most technical/compound exercises first (when CNS fresh)
2. Large muscle groups before small
3. Multi-joint before single-joint
4. Higher intensity before lower intensity

### Volume per Session
- 15-25 total working sets per session is typical
- 2-4 exercises per muscle group
- Quality over quantity - better to do fewer sets well

---

## WEIGHT SELECTION DECISION TREE:

For each exercise, follow this logic:

```
Has recent data (within 4 weeks)?
├── YES → Check last performance
│   ├── Hit target reps easily (RPE ≤7) → INCREASE (+2.5kg compound, +1-2kg isolation)
│   ├── Hit target reps, moderate effort (RPE 8) → STAY at same weight
│   ├── Reps declining in session (8,7,5) → STAY, focus on consistency
│   ├── Failed target reps → DECREASE (try previous successful weight)
│   └── Way below target → DECREASE significantly (10-20%)
│
└── NO → Start conservative
    ├── If have old data: ~70-80% of previous weight
    └── If new exercise: Start light, find working weight
```

---

## CRITICAL RULES:
1. For each exercise, look at "VALID WEIGHTS TO USE" - you can ONLY prescribe weights from that list
2. If no valid weights listed, recommend starting conservative (light weight)
3. NEVER invent or calculate weights - use EXACT numbers from the data

## DECISION WORD MUST MATCH WEIGHT CHANGE (VERY IMPORTANT):
- If you say "INCREASE from Xkg" → prescription MUST be > X
- If you say "DECREASE from Xkg" → prescription MUST be < X
- If you say "STAY at Xkg" → prescription MUST be = X

WRONG (DO NOT DO THIS):
- "INCREASE from 45kg" then prescribe 43kg ← WRONG! 43 < 45
- "DECREASE from 6.8kg" then prescribe 7.5kg ← WRONG! 7.5 > 6.8
- Prescribing a weight not in "VALID WEIGHTS TO USE" ← WRONG!

CORRECT:
- Check "VALID WEIGHTS TO USE: 40kg, 45kg, 50kg"
- "INCREASE from 45kg" then prescribe 50kg ← CORRECT! (50 is in valid list AND 50 > 45)

## OUTPUT FORMAT:

For each exercise:

### [Exercise Name]
**Prescription: [Weight]kg × [Reps] × [Sets]**
- **Decision**: [INCREASE/STAY/DECREASE/NEW] from [last weight] because [what data shows]
- **Rest**: [X] seconds
- **Cue**: [One technique tip]

End with:
**Session totals**: [X] working sets, ~[Y] minutes"""


TRAINING_SUMMARY_TEMPLATE = """## Task: Analyze training over last {weeks} weeks

## Overall Statistics
{training_stats}

## Per-Exercise Data
{recent_workouts}

---

## CRITICAL FORMATTING RULES:
- NO LaTeX or math notation (no \\frac, \\times, \\text)
- Use plain arithmetic: "6 ÷ 4 = 1.5" not "\\frac{{6}}{{4}}"
- SETS = count of sets (a number like 12), NOT weight in kg
- ONLY use numbers that appear in the data above

## HOW TO CALCULATE:
- Sessions/week = total sessions ÷ weeks (e.g., "8 sessions ÷ 4 weeks = 2/week")
- Sets/week = total sets for muscle ÷ weeks (e.g., "24 chest sets ÷ 4 weeks = 6 sets/week")
- Weight change % = ((end - start) ÷ start) × 100

---

## YOUR ANALYSIS:

### 1. Training Consistency
Calculate in plain text:
- Total sessions in data: [count from data]
- Sessions per week: [X] sessions ÷ {weeks} weeks = [Y] sessions/week
- Target: 3-5 sessions/week
- Assessment: [Adequate / Needs improvement]

### 2. Exercise Progress Table
ONLY include exercises from the data above. Quote exact weights.

| Exercise | First Weight | Last Weight | Change |
|----------|--------------|-------------|--------|
| [Name] | [X]kg | [Y]kg | [+Z%] or [no change] |

### 3. Volume Analysis
Count SETS (not kg). A "set" is one round of an exercise (e.g., "3 sets" = 3).

| Muscle | Sets in Period | Sets/Week | Target | Status |
|--------|----------------|-----------|--------|--------|
| [Name] | [X] sets | [X÷weeks] | 10-20 | [Low/OK/High] |

### 4. Top 3 Wins (quote actual data)
1. [Exercise]: [what happened with specific numbers from data]
2. ...
3. ...

### 5. Top 3 Action Items
1. [Exercise]: [specific recommendation with target weight/reps]
2. ...
3. ...

**Note**: These recommendations assume adequate recovery. If fatigue indicators are present (RPE creeping up, performance declining), prioritize recovery over progression.

---

## EXAMPLE GOOD OUTPUT:

### 1. Training Consistency
- Total sessions: 8 sessions in 4 weeks
- Frequency: 8 ÷ 4 = 2 sessions/week
- Target: 3-5 sessions/week
- Assessment: Below target, consider adding 1-2 sessions/week

### 2. Exercise Progress
| Exercise | First | Last | Change |
|----------|-------|------|--------|
| Bench Press | 60kg | 70kg | +16.7% |
| Squat | 80kg | 80kg | No change (plateau) |

### 3. Volume
| Muscle | Total Sets | Per Week | Target | Status |
|--------|------------|----------|--------|--------|
| Chest | 24 sets | 6/week | 10-20 | Low |
| Legs | 16 sets | 4/week | 10-20 | Low |

(Note: "24 sets" is a COUNT of sets performed, not kg)"""


RECOVERY_ANALYSIS_TEMPLATE = """## Task: Assess recovery and fatigue

## Training Data (Last 4 Weeks)
{training_data}

## Performance Indicators
{performance_indicators}

## Trends
- RPE trend: {rpe_trends}
- Volume trend: {volume_trends}
- Weight progression: {weight_trends}

---

## FATIGUE ASSESSMENT:

### Warning Signs Checklist:
| Signal | Present? | Evidence |
|--------|----------|----------|
| RPE creeping up at same weights | [Yes/No] | [Quote data] |
| Performance declining 2+ weeks | [Yes/No] | [Quote data] |
| Volume spike >20% recently | [Yes/No] | [Quote data] |

### Recovery Status: [GOOD / MODERATE / NEEDS DELOAD]

**GOOD** (all clear):
- Stable or improving performance
- RPE consistent
- No warning signs

**MODERATE** (minor adjustment needed):
- Some fatigue accumulation
- Consider: reduce volume 20% or add rest day

**NEEDS DELOAD** (take action):
- Multiple warning signs present
- Recommend: 5-7 day deload (50% volume OR 60% intensity)

---

## RECOMMENDATION:

**Status**: [GOOD/MODERATE/NEEDS DELOAD]

**Action**: [Specific recommendation based on status]

**Timeline**: [When to reassess]"""


def format_workout_history(history: list[dict], limit: int = 8) -> str:
    """Format workout history for prompt injection with detailed stats."""
    if not history:
        return "No workout history available."

    lines = []
    for i, workout in enumerate(history[-limit:], 1):
        date = workout.get("date")
        date_str = date.strftime("%Y-%m-%d") if date else "Unknown"

        sets = workout.get("sets", [])
        if sets:
            weights = [s.get('weight', 0) or 0 for s in sets]
            reps_list = [s.get('reps', 0) or 0 for s in sets]

            if weights and any(w > 0 for w in weights):
                max_weight = max(w for w in weights if w > 0)

                sets_detail = ", ".join(
                    f"{s.get('weight', 0)}kg×{int(s.get('reps', 0))}"
                    for s in sets if s.get('weight')
                )

                # Check for intra-session fatigue (declining reps)
                reps_trend = ""
                if len(reps_list) >= 3:
                    if reps_list[0] > reps_list[-1]:
                        reps_trend = " ⚠️ reps declining"
                    elif reps_list[-1] > reps_list[0]:
                        reps_trend = " ✓ reps increasing"

                lines.append(f"- {date_str}: {sets_detail}{reps_trend}")
            else:
                lines.append(f"- {date_str}: No weight data")
        else:
            lines.append(f"- {date_str}: No sets recorded")

    return "\n".join(lines)


def format_recent_workouts(history: list[dict], limit: int = 3) -> str:
    """Format recent workouts with set-by-set detail."""
    if not history:
        return "No recent workout data available."

    lines = []
    for workout in history[-limit:]:
        date = workout.get("date")
        date_str = date.strftime("%b %d, %Y") if date else "Unknown"
        lines.append(f"\n**{date_str}**")

        sets = workout.get("sets", [])
        if sets:
            total_volume = 0
            reps_list = []
            for i, s in enumerate(sets, 1):
                weight = s.get("weight", 0) or 0
                reps = s.get("reps", 0) or 0
                rpe = s.get("rpe")

                total_volume += weight * reps
                reps_list.append(reps)
                rpe_str = f" @RPE{rpe}" if rpe else ""
                lines.append(f"  Set {i}: {weight}kg × {reps}{rpe_str}")

            # Add intra-session analysis
            if len(reps_list) >= 2:
                if reps_list[0] > reps_list[-1] + 1:
                    lines.append(f"  → Note: Reps declined from {reps_list[0]} to {reps_list[-1]} (fatigue)")
                elif reps_list[-1] >= reps_list[0]:
                    lines.append(f"  → Note: Reps maintained/improved (good recovery)")
        else:
            lines.append("  No sets recorded")

    return "\n".join(lines)


def format_exercises_for_plan(exercises: list[dict]) -> str:
    """Format exercises with full historical context for workout planning."""
    if not exercises:
        return "No exercises defined for this day."

    lines = []
    for i, ex in enumerate(exercises, 1):
        name = ex.get("name", "Unknown")
        muscle = ex.get("muscle_group", "Unknown")
        rest = ex.get("rest_time", 120)
        ex_type = get_exercise_type(muscle, ex.get("equipment", ""))
        target_reps = "5-8" if ex_type == "compound" else "10-15"

        lines.append(f"\n### {i}. {name}")
        lines.append(f"- Type: {ex_type}, target: {target_reps} reps")

        # Collect ALL weights used for this exercise
        all_weights_used = set()

        # Get last 3 sessions for actual performance data
        last_3 = ex.get("last_3_sessions", [])
        last_sets = ex.get("last_sets", [])

        if last_3:
            lines.append("- **Recent sessions (oldest to newest)**:")
            for sess in last_3:
                date_str = sess["date"].strftime("%m/%d") if sess.get("date") else "?"
                weight = sess.get('weight', 0)
                reps = sess.get('avg_reps', 0)
                if weight:
                    all_weights_used.add(weight)
                    if reps:
                        lines.append(f"    {date_str}: {weight}kg × {reps:.1f} avg reps")
                    else:
                        lines.append(f"    {date_str}: {weight}kg (reps not recorded)")

            # Show last session set-by-set for detailed analysis
            if last_sets:
                sets_str = ", ".join(f"{s.get('weight', 0)}×{s.get('reps', 0)}" for s in last_sets if s.get('weight'))
                for s in last_sets:
                    if s.get('weight'):
                        all_weights_used.add(s['weight'])
                if sets_str:
                    lines.append(f"- **Last session sets**: {sets_str}")
        else:
            # No recent data
            last_weight = ex.get("last_weight")
            if last_weight:
                all_weights_used.add(last_weight)
                lines.append(f"- **Last weight used**: {last_weight}kg (no recent sessions)")
            else:
                lines.append("- **NO DATA** - start conservative, find working weight")

        # Add PR weight to valid options
        all_time_pr = ex.get("all_time_pr")
        if all_time_pr:
            all_weights_used.add(all_time_pr)
            lines.append(f"- All-time PR: {all_time_pr}kg")

        # EXPLICIT list of valid weights - LLM must pick from these
        if all_weights_used:
            sorted_weights = sorted(all_weights_used)
            weights_str = ", ".join(f"{w}kg" for w in sorted_weights)
            lines.append(f"- **VALID WEIGHTS TO USE**: {weights_str}")

    return "\n".join(lines)


def add_user_context(context: str = None) -> str:
    """Format optional user context."""
    if not context or not context.strip():
        return ""
    return f"\n## User Notes\n> {context.strip()}\n"


def get_exercise_type(muscle_group: str, equipment: str) -> str:
    """Determine if exercise is compound or isolation."""
    compound_muscles = ["chest", "back", "quadriceps", "hamstrings", "glutes"]
    compound_equipment = ["barbell", "squat", "deadlift", "bench", "row"]

    text = f"{muscle_group} {equipment}".lower()

    for indicator in compound_muscles + compound_equipment:
        if indicator in text:
            return "compound"

    return "isolation"


def get_rep_range_hint(exercise_type: str) -> str:
    """Get appropriate rep range for exercise type."""
    if exercise_type == "compound":
        return "5-8 reps (strength/hypertrophy)"
    else:
        return "10-15 reps (hypertrophy/endurance)"


def calculate_valid_range(last_weight: float) -> tuple[float, float]:
    """Calculate valid suggestion range (±10% of last weight)."""
    if not last_weight or last_weight <= 0:
        return (0, 0)
    min_valid = round(last_weight * 0.9, 1)
    max_valid = round(last_weight * 1.1, 1)
    return (min_valid, max_valid)


def parse_ai_recommendation(text: str) -> dict:
    """Parse AI recommendation text to extract structured output."""
    import re

    patterns = [
        r'\*\*(?:Recommended|Rx):\s*([0-9.]+)\s*kg\s*[×x]\s*([0-9.]+)\s*(?:reps?)?\s*[×x]\s*([0-9]+)',
        r'Recommended:\s*([0-9.]+)\s*kg\s*[×x]\s*([0-9.]+)\s*[×x]\s*([0-9]+)',
        r'(\d+\.?\d*)\s*kg\s*[×x]\s*(\d+)\s*(?:reps?)?\s*[×x]\s*(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            weight = float(match.group(1))
            reps = float(match.group(2))
            sets = int(match.group(3))

            # Extract reasoning (look for "Why:" section)
            why_match = re.search(r'\*\*Why\*\*:?\s*(.+?)(?:\*\*|$)', text, re.DOTALL)
            reasoning = why_match.group(1).strip() if why_match else ""

            return {
                "weight": weight,
                "reps": int(reps),
                "sets": sets,
                "reasoning": reasoning[:500],
                "short_answer": f"{weight}kg × {int(reps)} × {sets}"
            }

    return {
        "weight": None,
        "reps": None,
        "sets": None,
        "reasoning": text,
        "short_answer": None,
        "parsing_failed": True
    }
