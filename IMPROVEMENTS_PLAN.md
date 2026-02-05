# GymUp AI Trainer - Future Improvements Plan

## Issues to Fix (Priority Order)

### 1. Dashboard View Issues

#### 1.0 Fix Number Formatting (HIGH PRIORITY)
**Problem**: Recent workouts show truncated/malformed numbers:
- "2,5..." instead of full values
- "39..." truncated duration
- Volume showing incorrectly

**Root Cause**: Column widths too narrow for formatted numbers

**Solution**:
- Increase column widths in Recent Workouts section
- Format numbers consistently: `{value:,.1f}` for tonnage, `{value:.0f}` for duration
- Test with various number lengths

**File**: `ui/views/dashboard.py` lines 75-79

---

#### 1.1 AI Training Summary on App Startup (MEDIUM PRIORITY)
**Feature**: Automatic AI analysis of last 1-4 weeks training shown prominently on dashboard load

**What it should show**:
- Volume trends over the period
- Consistency assessment (workouts completed vs planned)
- Notable personal records hit
- Fatigue signals detected
- Key recommendations

**Implementation**:
- Call new function `generate_training_summary()` on dashboard load
- Cache result (don't regenerate on every tab switch)
- Display as expandable card at top of dashboard
- Include timestamp showing when last updated

**Files**:
- `ui/views/dashboard.py` (add summary section)
- `llm/functions.py` (add `generate_training_summary(db_path, weeks=4)`)
- `llm/prompts.py` (add `TRAINING_SUMMARY_TEMPLATE`)

**Prompt Template Should Include**:
```
Analyze training data from last N weeks:
- Total volume
- Number of workouts
- Exercise performance trends
- Any notable PRs
- Recovery patterns
- Recommendations for next phase
```

---

#### 1.2 Volume Distribution by Exercise (MEDIUM PRIORITY)
**Current State**: Shows volume by muscle group (good)

**Enhancement**: Add exercise-level breakdown
- Top 10 exercises by total volume
- Show muscle group for context
- Interactive: click to drill into exercise detail
- Display as table or bar chart below muscle distribution

**Implementation**:
- Query top exercises by tonnage: `query.get_top_exercises_by_volume(weeks=4, limit=10)`
- Create chart component: `create_exercise_volume_chart()`
- Add new section in dashboard between muscle distribution and weekly volume

**Files**:
- `db/queries.py` (add query method)
- `ui/components/charts.py` (add chart function)
- `ui/views/dashboard.py` (add new section)

---

### 2. Programs View Overhaul

#### 2.0 Current Problem
- Shows only program structure
- No actionable insights
- No way to plan or prepare workouts

---

#### 2.1 Add Useful Stats per Program (MEDIUM PRIORITY)
For each program, show:
- Total volume over lifetime
- Volume this month / this week
- Frequency adherence: planned workouts vs actual completed
- Progress per main exercise in program (top 3)
- Last session date

**Implementation**:
- Extend program cards with stats section
- Query: `query.get_program_stats(program_id)`
- Display in tabbed layout per program

---

#### 2.2 AI-Powered Workout Planner (HIGH PRIORITY)
**Feature**: "Plan Next Workout" button for each training day

**What it generates**:
- Exercises to perform
- Recommended weights (from AI, not just rule-based)
- Sets × reps × weight for each exercise
- Rest times between sets
- Warm-up recommendations
- Total estimated duration

**User Can**:
- Adjust any values
- Save as "planned workout" for tracking

**Implementation**:
- New button on each day card: "Plan Next Workout"
- Modal/form with user context input:
  - "How much time do you have?"
  - "How are you feeling?" (energy level)
  - Any injuries/concerns?
- Call: `plan_next_workout(day_id, user_context, time_available)`
- Display results in structured format
- "Save as Planned" button to record in database

**Files**:
- `ui/views/programs.py` (add planner UI)
- `llm/functions.py` (implement `plan_next_workout()`)
- `llm/prompts.py` (add `PLAN_NEXT_WORKOUT_TEMPLATE`)
- `db/queries.py` (add method to get day's exercises with recent performance)

**Prompt Template Should Include**:
```
Day: {day_name}
Exercises: {exercise_list}
Last session: {recent_performance}
User constraints: {time_available}, {feeling}, {concerns}
User notes: {user_context}

Generate detailed workout plan with:
1. Warm-up (sets, reps)
2. Main exercises (weight, reps, sets, rest times)
3. Notes for execution
4. Total duration estimate
```

---

### 3. Exercises View Improvements

#### 3.0 Sort by Session Count (HIGH PRIORITY)
**Current**: Exercises sorted alphabetically

**Change**: Default sort by most frequently trained
- User most trains exercises appear first
- Alphabetical fallback for exercises with same count

**Implementation**:
```python
# In queries.py - modify get_used_exercises()
def get_used_exercises(self) -> list[ThExercise]:
    # Get exercises with session counts
    # Sort by: count DESC, then name ASC
```

**File**: `db/queries.py` lines 378-398

---

#### 3.1 Default Trend Window: 4 Weeks (HIGH PRIORITY)
**Current**: Analyzes 12 weeks by default

**Change**: Default to 4 weeks (more recent/relevant)
- Show last 4 weeks of data prominently
- Option to adjust window if needed

**Implementation**:
```python
# In exercises.py line 90
history = query.get_exercise_history(selected_exercise.id, weeks=4)  # was 12
```

**Files**:
- `ui/views/exercises.py` line 90
- `analytics/progression.py` (update default parameter if used)

---

#### 3.2 Remove "Confidence: Medium" Display (HIGH PRIORITY)
**Problem**: Confusing without explanation

**Options**:
1. Remove entirely
2. Replace with meaningful metric: R² value, data point count, or trend strength

**Recommendation**: Remove from display but keep in data for future use

**Implementation**:
```python
# In exercises.py around line 211
# Remove this line:
# st.metric("Confidence", result.get("confidence", "N/A").title())
```

**File**: `ui/views/exercises.py` line 211 (remove or replace)

---

#### 3.3 Unified AI Recommendation Format (HIGH PRIORITY - COMPLEX)
**Problem**: Rule-based says "42.5 kg" but AI says something different. Inconsistent.

**Solution**: Single structured AI response with:
1. **Short Answer** (numbers): `Recommended: 42.5 kg × 8 reps × 3 sets`
2. **Long Answer** (collapsible): Full explanation with reasoning

**Current Flow**:
- Rule-based: `suggest_next_weight()` → returns number
- AI: `suggest_next_weights()` → returns verbose explanation
- Display: Shows both separately (confusing)

**New Flow**:
- AI system prompt enforces structured output
- Force AI to suggest same weight as rule-based when aligned
- If different: AI explains why (e.g., fatigue detected, form issues)

**Implementation**:

1. **Update `llm/prompts.py`**:
   - Modify `SUGGEST_WEIGHTS_TEMPLATE` to include structured output format
   - Add instruction: Start response with `**Recommended: X kg × Y reps × Z sets**`

2. **Update `llm/functions.py`**:
   - `suggest_next_weights()` should:
     - Get rule-based suggestion
     - Include it in prompt as baseline
     - Ask AI if it agrees or has concerns
     - Parse response to extract structured recommendation
     - Return both short + long form

3. **Update `ui/views/exercises.py`**:
   - Display as:
     ```
     ✅ Recommended: 42.5 kg × 8 reps × 3 sets

     [Expand] Reasoning
     [Expanded]
     Last session: 40kg × 8,8,7 (RPE 7-8)
     Trend: +2.5kg/week for 3 weeks
     Ready for progression based on consistent performance...
     ```

**Sample Prompt Template**:
```
**Exercise**: {exercise_name}
**Recent Performance**: {recent_workouts}
**Baseline Suggestion**: {rule_based_weight} kg × {rule_based_reps}

User context: {user_context}

Analyze the baseline suggestion and provide:
1. Agreement or concerns with baseline
2. Final recommendation: **X kg × Y reps × Z sets**
3. Detailed reasoning (2-3 sentences)
4. Alternative approach if fatigued
5. Warning signs to watch

Format your recommendation clearly at the start of response.
```

**Files**:
- `llm/prompts.py` (update template + add parser hints)
- `llm/functions.py` (enhance `suggest_next_weights()`)
- `ui/views/exercises.py` (update display logic, lines 200-220)

---

### 4. Analytics View → Merge with Dashboard

#### 4.0 Current Problem
- Duplicate functionality with dashboard
- "Recovery & Fatigue Analysis" unclear
- "Confidence: Medium" unexplained
- No actionable insights

#### 4.1 Solution
- Remove Analytics tab entirely
- Move useful metrics to Dashboard as collapsible sections
- Replace rule-based fatigue detection with AI-powered analysis

**AI Recovery & Fatigue Section** (in Dashboard):
- Analyze RPE trends last 4 weeks
- Detect overreaching signals
- Assess sleep/recovery indicators (if available)
- Provide actionable recommendations:
  - "Keep pushing - good recovery"
  - "Consider deload week soon"
  - "Take 1-2 rest days"
  - etc.

**Implementation**:
- New LLM function: `analyze_recovery_status(db_path, weeks=4)`
- Add to dashboard as collapsible expander below AI summary
- Call on load but cache result

**Files**:
- `ui/app.py` (remove Analytics from navigation)
- `ui/views/dashboard.py` (add recovery section)
- `llm/functions.py` (add `analyze_recovery_status()`)
- Delete: `ui/views/analytics.py`

---

## Implementation Priority

### Tier 1 - High Impact, Lower Effort (Start Here)
1. Fix dashboard number formatting (1.0)
2. Sort exercises by session count (3.0)
3. Default trend to 4 weeks (3.1)
4. Remove "Confidence: Medium" display (3.2)

### Tier 2 - High Impact, Medium Effort (Next)
5. Unified AI recommendation format (3.3)
6. AI workout planner for Programs (2.2)
7. AI training summary on startup (1.1)

### Tier 3 - Good to Have (Later)
8. Volume by exercise chart (1.2)
9. Program stats per program (2.1)
10. Merge Analytics into Dashboard (4.1)

---

## Testing Checklist

After each change:
```bash
gymup-tracker start --db ./workout.db
```

### 1.0 - Dashboard Formatting
- [ ] Recent Workouts: volume shows full number (e.g., "12,450 kg")
- [ ] Duration shows full number (e.g., "75 min")
- [ ] No truncation with "..."

### 3.0 - Exercise Sorting
- [ ] Exercises list sorted by most sessions first
- [ ] Most trained exercise appears at top

### 3.1 - 4-Week Default
- [ ] Exercises page shows 4 weeks of data by default
- [ ] Charts load faster (less data)

### 3.2 - Remove Confidence
- [ ] "Confidence: Medium" text removed from UI
- [ ] No visual regression

### 3.3 - Unified AI Format
- [ ] Suggested weight displayed prominently
- [ ] Long explanation in expandable section
- [ ] Short answer format: "42.5 kg × 8 reps × 3 sets"

---

## Files Summary

| File | Changes |
|------|---------|
| `ui/views/dashboard.py` | Fix formatting (1.0), add AI summary (1.1), add exercise volume (1.2), add recovery analysis (4.1) |
| `ui/views/exercises.py` | Remove confidence display (3.2), unified AI format (3.3) |
| `ui/views/programs.py` | Add program stats (2.1), add workout planner (2.2) |
| `ui/app.py` | Remove Analytics from nav (4.1) |
| `db/queries.py` | Sort exercises by count (3.0), add new query methods |
| `llm/functions.py` | New functions: `generate_training_summary()`, `plan_next_workout()`, `analyze_recovery_status()` |
| `llm/prompts.py` | New templates for above functions, update SUGGEST_WEIGHTS with structured format |
| `ui/components/charts.py` | Add exercise volume chart component |
| `analytics/progression.py` | Update default window to 4 weeks if needed |

---

## Notes

- All changes maintain backward compatibility
- Only performed workouts are analyzed (filtered correctly already)
- UI improvements focus on clarity and reducing cognitive load
- AI enhancements provide actionable, evidence-based recommendations
- Keep it simple: avoid feature creep beyond these improvements
