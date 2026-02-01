# GymUp Workout Tracker & AI Training Assistant

A comprehensive workout analysis and AI-powered training recommendation system that parses GymUp SQLite databases to provide intelligent workout progression suggestions.

## Project Overview

This project provides a complete solution for analyzing GymUp workout data, visualizing training progress, and generating personalized weight progression recommendations using a locally-hosted LLM. The system intelligently analyzes your training history, identifies patterns, and suggests optimal weights for your next workout with detailed reasoning.

## Core Functionality

### 1. Workout Data Browser
- **Program Management**: View all training programs with detailed information
- **Exercise Catalog**: Browse exercises with muscle groups, equipment, and technique guides
- **Training History**: Track all workouts with timestamps, sets, reps, and weights
- **Progress Trends**: Visualize weight progression, volume, and performance metrics over time

### 2. AI-Powered Weight Recommendations
- **Smart Progression**: Analyze historical performance to suggest next weights
- **Contextual Reasoning**: LLM explains recommendations based on:
  - Recent performance trends
  - Progressive overload principles
  - Recovery patterns and rest periods
  - Personal strength curves and plateaus
  - Exercise-specific considerations
- **Per-Exercise Analysis**: Customized recommendations for each movement pattern
- **Per-Program Optimization**: Holistic view of program progression

## Database Schema

### Key Tables

#### `program`
Training programs with metadata:
- `name`, `comment`, `userComment`: Program details
- `purpose`, `level`, `frequency`: Program characteristics
- `place`, `gender`: Training context

#### `day`
Individual workout days within programs:
- `program_id`: Links to parent program
- `name`, `comment`: Day identification
- `order_num`: Sequence in program

#### `th_exercise` (Exercise Templates)
Exercise definitions:
- `name`, `guide`: Exercise identification and instructions
- `mainMuscleWorked`, `otherMuscles`: Target muscle groups
- `equipment`, `mechanicsType`: Movement characteristics
- `level`, `type`, `force`: Exercise attributes

#### `exercise`
Exercise instances in program days:
- `day_id`: Links to workout day
- `th_exercise_id`: Links to exercise template
- `restTime`, `restTimeAfterExercise`: Recovery parameters
- `isMeasureWeight`, `isMeasureReps`, etc.: Tracking flags
- `oneRepMax`: Calculated 1RM

#### `training`
Completed workout sessions:
- `startDateTime`, `finishDateTime`: Session timing
- `day_id`: Links to program day
- `tonnage`, `repsAmount`, `setsAmount`: Volume metrics
- `hard_sense`: Subjective difficulty rating

#### `workout`
Exercise instances within training sessions:
- `training_id`: Links to training session
- `th_exercise_id`: Exercise performed
- `tonnage`, `setsAmount`, `repsAmount`: Performance data
- `oneRepMax`: Session-specific 1RM
- `hard_sense`: Exercise difficulty

#### `set_`
Individual sets within workouts:
- `workout_id`: Links to workout
- `weight`, `reps`: Performance data
- `time`, `distance`: Alternative metrics
- `finishDateTime`: Set completion timestamp
- `hard_sense`: Set difficulty

## Technical Architecture

### Data Layer
```
GymUp SQLite Database (workout.db)
├── Schema Parser (SQLite3 / SQLAlchemy)
├── Data Validation & Cleaning
├── Google Drive Integration (via PyDrive2 or gdown)
└── Query Optimization for Time-Series Analysis
```

### Analysis Engine
```
Training Analytics Module
├── Progression Calculator
│   ├── Linear regression for weight trends
│   ├── Volume accumulation tracking
│   └── Fatigue detection algorithms
├── Performance Metrics
│   ├── 1RM estimation (Epley, Brzycki formulas)
│   ├── Volume calculations (tonnage, sets×reps)
│   └── Intensity tracking (RPE, % of 1RM)
└── Pattern Recognition
    ├── Plateau detection
    ├── Overreaching indicators
    └── Recovery assessment
```

### LLM Integration Layer
```
Local LLM Service (LM Studio / Ollama / llamafile)
├── Model: Recommend 7B-13B parameter models
│   ├── Mistral 7B / Mixtral 8x7B
│   ├── Llama 3 8B / 70B
│   └── DeepSeek-Coder (for structured reasoning)
├── Predefined Analysis Functions (No Chat Interface)
│   ├── analyze_exercise_progression(exercise_id, context_weeks)
│   ├── suggest_next_weights(exercise_id, user_context)
│   ├── analyze_training_day(day_id, recent_sessions)
│   ├── suggest_next_day_plan(day_id, recovery_status, user_notes)
│   ├── detect_form_breakdown(exercise_id, rpe_trend)
│   ├── recommend_deload_week(program_id, fatigue_markers)
│   └── optimize_exercise_order(day_id, muscle_recovery)
└── API Interface
    ├── OpenAI-compatible endpoint
    ├── Request batching for efficiency
    └── Response parsing & validation
```

### Presentation Layer
```
UI Options (Choose one based on preference)

Option A: HTMX + FastAPI (Recommended for Snappy Interactions)
├── FastAPI Backend
│   ├── RESTful endpoints for data
│   ├── HTMX partial HTML responses
│   ├── Server-Sent Events for LLM streaming
│   └── Static file serving (CSS, JS)
├── HTMX Frontend
│   ├── Zero JavaScript for most interactions
│   ├── Progressive enhancement
│   ├── Inline loading states
│   └── Smooth partial page updates
├── Visualization
│   ├── Plotly.js (embedded in HTML)
│   ├── Chart.js (lightweight alternative)
│   └── Alpine.js for client-side interactivity
└── Styling
    ├── Tailwind CSS (utility-first)
    └── DaisyUI (component library)

Option B: Streamlit (Recommended for Rapid Prototyping)
├── Single Python File App
├── Built-in Components
│   ├── Sidebar for navigation
│   ├── Tabs for different views
│   ├── Expandable sections
│   └── Built-in charts (Plotly, Altair)
├── State Management
│   ├── Session state for context
│   └── Cache for expensive computations
└── Custom Components (if needed)
    ├── streamlit-aggrid for tables
    └── streamlit-extras for UI enhancements

CLI Launcher (Both Options)
├── Click/Typer for CLI interface
├── Database path argument (local or Google Drive URL)
├── Configuration validation
├── Auto-start web server
└── Browser auto-open
```

## LLM Recommendation System

### Predefined LLM Functions (No Chat Interface)

The LLM integration is designed around specific, actionable analysis functions rather than open-ended chat. Each function has a well-defined purpose and structured output.

#### Exercise-Level Functions

**1. `analyze_exercise_progression`**
- **Input**: Exercise ID, number of weeks to analyze, optional user context
- **Output**: Structured analysis of progression trend
- **Use Case**: Click "Analyze Progression" button on exercise detail page
- **LLM Task**: Identify trends (linear progression, plateau, regression), highlight PRs, detect patterns
- **User Context Examples**: "Shoulder pain last week", "Switched to wider grip", "Added pause reps"

**2. `suggest_next_weights`**
- **Input**: Exercise ID, recent workout data, user context (optional)
- **Output**: Specific weight recommendation with reasoning
- **Use Case**: Planning next workout session
- **LLM Task**: Apply progressive overload principles, account for fatigue, suggest rep ranges
- **User Context Examples**: "Feeling strong today", "Coming back from vacation", "Low sleep this week"

**3. `detect_form_breakdown`**
- **Input**: Exercise ID, RPE trends, video notes (if available)
- **Output**: Form degradation warning with recommendations
- **Use Case**: Automatic trigger when RPE increases without weight changes
- **LLM Task**: Analyze if high RPE suggests form issues vs genuine strength limits
- **User Context Examples**: "Lower back fatigue", "Bar path felt off", "Elbow pain"

**4. `suggest_exercise_alternatives`**
- **Input**: Exercise ID, reason for substitution, equipment available
- **Output**: 3-5 alternative exercises with reasoning
- **Use Case**: Injury management or equipment unavailability
- **LLM Task**: Match muscle targets, movement patterns, and training stimulus
- **User Context Examples**: "Knee pain on squats", "No barbell available", "Home gym setup"

#### Training Day-Level Functions

**5. `analyze_training_day`**
- **Input**: Day ID, last 5 sessions of this day, performance metrics
- **Output**: Comprehensive day performance analysis
- **Use Case**: Review button on day detail page
- **LLM Task**: Evaluate volume trends, exercise balance, recovery patterns
- **User Context Examples**: "Time-constrained workouts lately", "Added cardio after lifting", "Changed rest times"

**6. `suggest_next_day_plan`**
- **Input**: Day ID, recovery status, user notes, upcoming schedule
- **Output**: Detailed workout plan with weights, sets, reps, rest times
- **Use Case**: "Generate Next Workout" button
- **LLM Task**: Balance progression across exercises, manage fatigue, adjust volume
- **User Context Examples**: "Only have 45 minutes", "Legs still sore from last session", "Want to PR today"

**7. `optimize_exercise_order`**
- **Input**: Day ID, current exercise sequence, fatigue patterns
- **Output**: Reordered exercise list with reasoning
- **Use Case**: Program design optimization
- **LLM Task**: Prioritize compound movements, manage muscle pre-fatigue, optimize energy systems
- **User Context Examples**: "Struggling on bench after shoulders", "Want to prioritize deadlift"

#### Program-Level Functions

**8. `recommend_deload_week`**
- **Input**: Program ID, fatigue markers (RPE trends, volume accumulation)
- **Output**: Deload timing and intensity recommendations
- **Use Case**: Automatic suggestion when fatigue detected
- **LLM Task**: Identify overreaching signs, suggest deload protocol (intensity vs volume reduction)
- **User Context Examples**: "Sleep quality declining", "Persistent muscle soreness", "Motivation low"

**9. `evaluate_program_balance`**
- **Input**: Program ID, muscle group distribution, volume per muscle
- **Output**: Balance assessment with rebalancing suggestions
- **Use Case**: Periodic program review (monthly)
- **LLM Task**: Check push/pull ratio, upper/lower split, volume landmarks per muscle
- **User Context Examples**: "Focusing on bench press PR", "Want more posterior chain work"

**10. `predict_plateau_risk`**
- **Input**: Program ID, recent progression rates, training age
- **Output**: Plateau risk score with preventive measures
- **Use Case**: Proactive programming adjustment
- **LLM Task**: Analyze velocity of progression, compare to typical adaptation curves
- **User Context Examples**: "Been running this program 12 weeks", "Linear progression slowing"

### User Context Integration

Every LLM function accepts optional user context through a text input field:

```
┌─────────────────────────────────────────┐
│ 📊 Analyze Exercise Progression         │
├─────────────────────────────────────────┤
│ Exercise: Barbell Bench Press           │
│ Analyze last: [8] weeks                 │
│                                          │
│ 💬 Additional Context (Optional)        │
│ ┌─────────────────────────────────────┐ │
│ │ Shoulder pain resolved last week,   │ │
│ │ switched to closer grip, feeling    │ │
│ │ stronger                            │ │
│ └─────────────────────────────────────┘ │
│                                          │
│ [Analyze Progression] [Cancel]          │
└─────────────────────────────────────────┘
```

The context is injected into the LLM prompt to provide personalized analysis that accounts for factors not visible in raw data (injuries, technique changes, life stress, etc.).

### Prompt Architecture

#### System Prompt
```markdown
You are an expert strength & conditioning coach analyzing workout data.
Your role is to provide evidence-based weight progression recommendations.

Key principles:
- Progressive overload: 2.5-5% weight increases when performance is consistent
- Deload consideration: Suggest lighter weights if detecting fatigue patterns
- Exercise specificity: Different progressions for compound vs isolation movements
- Safety first: Conservative recommendations for complex movements
- Individual variability: Account for recent performance trends

Output format: Provide recommended weight with clear reasoning referencing:
1. Recent performance data (last 3-5 workouts)
2. Training principles applied
3. Specific concerns or considerations
```

#### Context Injection Example
```json
{
  "exercise": "Barbell Bench Press",
  "exercise_type": "compound",
  "main_muscle": "chest",
  "recent_workouts": [
    {
      "date": "2026-01-27",
      "sets": [
        {"weight": 80, "reps": 8, "rpe": 7},
        {"weight": 80, "reps": 8, "rpe": 7},
        {"weight": 80, "reps": 7, "rpe": 8}
      ],
      "rest_time_avg": 180
    },
    {
      "date": "2026-01-24",
      "sets": [
        {"weight": 80, "reps": 8, "rpe": 8},
        {"weight": 80, "reps": 7, "rpe": 8},
        {"weight": 80, "reps": 6, "rpe": 9}
      ],
      "rest_time_avg": 200
    },
    {
      "date": "2026-01-20",
      "sets": [
        {"weight": 77.5, "reps": 9, "rpe": 7},
        {"weight": 77.5, "reps": 8, "rpe": 8},
        {"weight": 77.5, "reps": 8, "rpe": 8}
      ],
      "rest_time_avg": 180
    }
  ],
  "current_1rm_estimate": 100,
  "user_notes": "Feeling strong, shoulders recovered"
}
```

#### Expected Output Format
```json
{
  "recommended_weight": 82.5,
  "confidence": "high",
  "reasoning": {
    "summary": "Recommend increasing to 82.5kg based on consistent performance at 80kg",
    "analysis": [
      "Recent trend: Successfully completed 3 sets of 8+ reps at 80kg on Jan 27",
      "Progression rate: 3.1% increase aligns with conservative progression for compound movements",
      "RPE management: Previous session RPE 7-8 indicates capacity for slight increase",
      "Recovery: Improved performance from Jan 24 to Jan 27 suggests adequate recovery",
      "Volume strategy: Target 3×8 reps at 82.5kg, expect RPE 8-9 on final set"
    ],
    "alternative": "If fatigued, maintain 80kg and aim for 3×9-10 reps to build work capacity",
    "deload_signal": "Consider deload if unable to complete 6+ reps on first set"
  }
}
```

### Implementation Considerations

#### Model Selection
- **7B Models** (Mistral 7B, Llama 3 8B): Fast inference, suitable for per-exercise recommendations
- **13B+ Models** (Mixtral 8x7B, Llama 3 70B): Better reasoning for complex progression decisions
- **Quantization**: Use Q4_K_M or Q5_K_M for balance of speed and quality
- **Context Window**: Minimum 4K tokens for adequate history injection

#### Inference Optimization
- **Batching**: Process multiple exercises in single request when analyzing full program
- **Caching**: Store LLM responses with cache key = (exercise_id, last_5_workouts_hash)
- **Fallback**: Rule-based recommendations if LLM unavailable
- **Latency Target**: <3 seconds for single recommendation, <10 seconds for full program

#### Prompt Engineering Tips
1. **Few-shot examples**: Include 2-3 example analyses in system prompt
2. **Structured output**: Use JSON schema validation or instructor library
3. **Temperature**: 0.2-0.4 for consistent, conservative recommendations
4. **Max tokens**: 300-500 for detailed reasoning without verbosity
5. **Stop sequences**: Use newlines or delimiters to prevent rambling

## Development Roadmap

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Database schema exploration and ORM setup
- [ ] Basic data extraction queries (programs, exercises, workouts)
- [ ] Data validation and type conversion utilities
- [ ] Unit tests for database layer

### Phase 2: Analytics Engine (Week 2-3)
- [ ] Time-series analysis for weight progression
- [ ] 1RM estimation algorithms
- [ ] Volume and intensity metrics calculation
- [ ] Trend detection (plateaus, overreaching)
- [ ] Performance visualization (matplotlib/plotly)

### Phase 3: LLM Integration (Week 3-4)
- [ ] Local LLM setup documentation (LM Studio/Ollama)
- [ ] OpenAI-compatible client implementation
- [ ] Prompt template system with Jinja2
- [ ] Context builder for workout history
- [ ] Response parser and validator
- [ ] Error handling and fallback logic

### Phase 4: Recommendation System (Week 4-5)
- [ ] Per-exercise recommendation endpoint
- [ ] Per-program holistic analysis
- [ ] Confidence scoring based on data quality
- [ ] A/B testing framework for prompt variations
- [ ] Recommendation tracking and feedback loop

### Phase 5: User Interface (Week 5-6)
- [ ] CLI tool with Rich for terminal UI
- [ ] Web dashboard with FastAPI + React
- [ ] Interactive charts for progress tracking
- [ ] Recommendation cards with collapsible reasoning
- [ ] Export functionality (PDF/CSV)

### Phase 6: Polish & Optimization (Week 6-7)
- [ ] Performance profiling and optimization
- [ ] Comprehensive documentation
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] User testing and feedback incorporation

## Installation & Setup

### Prerequisites
```bash
# Python 3.10+
python --version

# Local LLM runtime (choose one)
# Option 1: LM Studio (GUI, easiest)
# Download from https://lmstudio.ai

# Option 2: Ollama (CLI, lightweight)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull mistral:7b-instruct

# Option 3: llamafile (single binary)
# Download from https://github.com/Mozilla-Ocho/llamafile
```

### Project Setup
```bash
# Clone repository
git clone https://github.com/yourusername/gymup-ai-trainer.git
cd gymup-ai-trainer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Quick Start - CLI Launcher

The application starts with a single CLI command that launches the web UI:

```bash
# Start with local database
gymup-tracker start --db ./data/workout.db

# Start with Google Drive database (auto-downloads)
gymup-tracker start --db "https://drive.google.com/file/d/YOUR_FILE_ID/view"

# Custom LLM endpoint
gymup-tracker start --db ./data/workout.db --llm-url http://localhost:1234/v1

# Specify UI framework
gymup-tracker start --db ./data/workout.db --ui streamlit  # or 'htmx'

# Full options
gymup-tracker start \
  --db ./data/workout.db \
  --llm-url http://localhost:1234/v1 \
  --llm-model mistral-7b-instruct \
  --ui htmx \
  --port 8000 \
  --no-browser  # Don't auto-open browser
```

**What happens:**
1. Validates database path (downloads if Google Drive URL)
2. Checks LLM endpoint connectivity
3. Starts web server (FastAPI/Streamlit)
4. Opens browser to http://localhost:8000
5. Shows dashboard with programs/exercises/analytics

### First-Time Configuration

On first run, you'll be prompted to configure:

```
🏋️  GymUp AI Trainer - First Time Setup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Database Location
  [1] Local file path
  [2] Google Drive URL
  
Choice: 1
Path: ./data/workout.db

LLM Configuration
  Endpoint: http://localhost:1234/v1
  Test connection... ✓ Connected
  Available models:
    [1] mistral-7b-instruct-v0.2
    [2] llama-3-8b-instruct
  
Choice: 1

UI Framework
  [1] HTMX (Recommended - Fast, lightweight)
  [2] Streamlit (Rapid prototyping)
  
Choice: 1

✓ Configuration saved to ~/.gymup-tracker/config.yaml
🚀 Starting server at http://localhost:8000...
🌐 Opening browser...
```

### Manual Configuration

Edit `~/.gymup-tracker/config.yaml`:

```yaml
database:
  path: "./data/workout.db"
  auto_backup: true
  backup_dir: "~/.gymup-tracker/backups"
  google_drive:
    enabled: false
    file_id: null
    credentials_path: "~/.gymup-tracker/gdrive_credentials.json"

llm:
  provider: "lm_studio"  # or "ollama", "llamafile", "openai"
  base_url: "http://localhost:1234/v1"
  model: "mistral-7b-instruct-v0.2"
  temperature: 0.3
  max_tokens: 500
  timeout: 30
  fallback_to_rules: true  # Use rule-based recommendations if LLM fails

analytics:
  min_workouts_for_recommendation: 3
  plateau_threshold_weeks: 2
  conservative_progression: true
  use_rpe: true
  cache_llm_responses: true
  cache_ttl_hours: 24

ui:
  framework: "htmx"  # or "streamlit"
  port: 8000
  auto_open_browser: true
  theme: "dark"  # or "light"
  chart_library: "plotly"  # or "chartjs"
  items_per_page: 20
  show_advanced_metrics: true

logging:
  level: "INFO"
  file: "~/.gymup-tracker/logs/app.log"
  max_size_mb: 10
  backup_count: 5
```

## Usage - Web UI Walkthrough

### Main Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│ 🏋️ GymUp AI Trainer              [⚙️ Settings] [🔌 LLM: ✓] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 Overview                                                 │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐ │
│  │ Total        │ This Week    │ This Month   │ All-Time  │ │
│  │ Workouts     │ Tonnage      │ PRs          │ 1RM Total │ │
│  │ 247          │ 12,450 kg    │ 8            │ 1,247 kg  │ │
│  └──────────────┴──────────────┴──────────────┴───────────┘ │
│                                                              │
│  🗂️ Programs                               [View All →]     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Push/Pull/Legs                              [Active ✓] │ │
│  │ 3x/week • Intermediate • 12 weeks running              │ │
│  │ [View Details] [Analyze Program] [Next Workout]        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  📈 Recent Trends                                            │
│  [Chart: Weight progression last 30 days - top 5 exercises] │
│                                                              │
│  🤖 AI Insights                                              │
│  ⚠️  Bench Press: Plateau detected (3 weeks at 80kg)        │
│      [Analyze] [Get Suggestions]                            │
│  ✓  Squat: Strong progression (+5kg/week for 4 weeks)       │
│  ⚡ Deadlift: Deload recommended based on RPE trends         │
│      [View Analysis] [Plan Deload]                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Exercise Detail View

Click any exercise to see detailed analytics:

```
┌─────────────────────────────────────────────────────────────┐
│ ← Back to Day                      Barbell Bench Press       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  💪 Current Stats                                            │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐ │
│  │ Est. 1RM     │ Last Session │ Total Volume │ Best Set  │ │
│  │ 100 kg       │ 80kg × 8     │ 24,560 kg    │ 85kg × 6  │ │
│  └──────────────┴──────────────┴──────────────┴───────────┘ │
│                                                              │
│  📊 Progression Chart (Last 12 weeks)                        │
│  [Interactive Plotly chart: Weight × Reps over time]         │
│                                                              │
│  🤖 AI Actions                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 💬 Additional Context (Optional)                       │ │
│  │ ┌──────────────────────────────────────────────────────┤ │
│  │ │ Shoulder fully recovered, switched to wider grip    │ │
│  │ └──────────────────────────────────────────────────────┤ │
│  │                                                          │ │
│  │ [🔍 Analyze Progression] [⚡ Suggest Next Weights]      │ │
│  │ [🔄 Find Alternatives]   [⚠️  Check Form Breakdown]     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  📝 Recent Workouts                        [Load More ↓]     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Jan 27, 2026 • 15:30                                   │ │
│  │ Set 1: 80kg × 8 (RPE 7) ⏱️ 3:00 rest                   │ │
│  │ Set 2: 80kg × 8 (RPE 7) ⏱️ 3:00 rest                   │ │
│  │ Set 3: 80kg × 7 (RPE 8)                                │ │
│  │ 💬 "Bar path felt solid, no shoulder pain"             │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### LLM Analysis Results

After clicking "Analyze Progression":

```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 AI Analysis: Barbell Bench Press Progression              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 Analysis Period: Last 8 weeks                            │
│  🗣️  User Context: "Shoulder fully recovered, switched to   │
│                     wider grip"                              │
│                                                              │
│  ✅ Overall Assessment: Strong Linear Progression            │
│                                                              │
│  Key Findings:                                               │
│  • Consistent 2.5kg increases every 2 weeks                  │
│  • Volume maintained at 3×8 with RPE 7-8                     │
│  • Recovery appears adequate (no RPE creep within sessions)  │
│  • Wider grip change (per user note) hasn't disrupted       │
│    progression - good sign of adaptation                     │
│                                                              │
│  Strengths:                                                  │
│  ✓ Steady tonnage increase (15% over 8 weeks)               │
│  ✓ Rest periods stable at 3 minutes                         │
│  ✓ No failed reps in last 10 sessions                       │
│                                                              │
│  Areas to Monitor:                                           │
│  ⚠️  RPE on final set consistently 8-9 (nearing limit)       │
│  ⚠️  Weight stalled at 80kg for last 2 sessions              │
│                                                              │
│  🎯 Recommendations:                                         │
│  1. Continue current progression - ready for next jump       │
│  2. Consider micro-loading (1.25kg plates) for sustainability│
│  3. Monitor shoulder with wider grip - add warm-up sets      │
│     if any discomfort returns                                │
│                                                              │
│  [Get Weight Suggestion] [Export Analysis] [Close]          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Weight Suggestion Modal

Click "Suggest Next Weights":

```
┌─────────────────────────────────────────────────────────────┐
│ ⚡ Next Workout Recommendation: Barbell Bench Press          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🎯 Recommended Weight: 82.5 kg                              │
│  📊 Confidence: High                                         │
│                                                              │
│  📋 Suggested Plan:                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Warm-up:                                               │ │
│  │   • Empty bar × 10                                     │ │
│  │   • 40kg × 8                                           │ │
│  │   • 60kg × 5                                           │ │
│  │   • 70kg × 3                                           │ │
│  │                                                          │ │
│  │ Working Sets:                                            │ │
│  │   • Set 1: 82.5kg × 8 (target RPE 8)                   │ │
│  │   • Rest 3:00                                           │ │
│  │   • Set 2: 82.5kg × 7-8 (target RPE 8-9)               │ │
│  │   • Rest 3:00                                           │ │
│  │   • Set 3: 82.5kg × 6+ (AMRAP, RPE 9)                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  💡 Reasoning:                                               │
│  • Last session: 3×8 at 80kg with RPE 7-8 indicates room    │
│    for progression                                           │
│  • 3.1% increase aligns with conservative compound movement │
│    progression                                               │
│  • Wider grip adaptation successful (per user note) -       │
│    biomechanics stabilized                                   │
│  • If final set drops below 6 reps, weight is appropriate   │
│                                                              │
│  ⚙️  Alternative Approach:                                   │
│  If feeling fatigued or shoulder concerns return:            │
│  • Stay at 80kg and push for 3×10 reps                      │
│  • Focus on bar speed and form                              │
│  • Next session attempt 82.5kg with higher confidence       │
│                                                              │
│  [Copy to Clipboard] [Export PDF] [Close]                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Training Day Overview

```
┌─────────────────────────────────────────────────────────────┐
│ ← Back to Program                        Push Day (Day A)    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📋 Exercises (6)                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. Barbell Bench Press       Last: 80kg×8  [View →]   │ │
│  │ 2. Incline Dumbbell Press    Last: 30kg×10 [View →]   │ │
│  │ 3. Overhead Press            Last: 50kg×6  [View →]   │ │
│  │ 4. Lateral Raises            Last: 12kg×15 [View →]   │ │
│  │ 5. Tricep Pushdowns          Last: 30kg×12 [View →]   │ │
│  │ 6. Cable Flyes               Last: 15kg×15 [View →]   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  📊 Day Performance (Last 5 Sessions)                        │
│  [Chart: Total volume, duration, avg RPE over time]          │
│                                                              │
│  🤖 AI Actions                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 💬 Additional Context                                  │ │
│  │ ┌──────────────────────────────────────────────────────┤ │
│  │ │ Only have 60 minutes today, need efficient workout  │ │
│  │ └──────────────────────────────────────────────────────┤ │
│  │                                                          │ │
│  │ [🔍 Analyze Day Performance]                            │ │
│  │ [📝 Generate Next Workout Plan]                         │ │
│  │ [🔄 Optimize Exercise Order]                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  🗓️ Recent Sessions                                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Jan 27, 2026 • 75 min • Tonnage: 5,240kg • RPE: 7.5   │ │
│  │ Jan 24, 2026 • 80 min • Tonnage: 5,180kg • RPE: 8.0   │ │
│  │ Jan 20, 2026 • 72 min • Tonnage: 4,960kg • RPE: 7.0   │ │
│  │                                                 [More ↓]│ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Generated Workout Plan

After clicking "Generate Next Workout Plan":

```
┌─────────────────────────────────────────────────────────────┐
│ 📝 AI-Generated Workout Plan: Push Day (Day A)               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ⏱️  Estimated Duration: 55-60 minutes (optimized for your  │
│     time constraint)                                         │
│  🗣️  User Context: "Only have 60 minutes today, need        │
│                     efficient workout"                       │
│                                                              │
│  🔧 Adjustments Made:                                        │
│  • Reduced rest times to 2:00-2:30 (from 3:00)             │
│  • Combined push movements into supersets where appropriate  │
│  • Removed one accessory exercise (cable flyes)              │
│                                                              │
│  📋 Workout Plan:                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ A1. Barbell Bench Press                                │ │
│  │     82.5kg × 8, 8, 6+ (AMRAP)                          │ │
│  │     Rest: 2:30 between sets                             │ │
│  │     [Reasoning: Primary movement - maintain intensity]  │ │
│  │                                                          │ │
│  │ A2. Overhead Press                                      │ │
│  │     52.5kg × 6, 6, 5                                    │ │
│  │     Rest: 2:30 between sets                             │ │
│  │     [Reasoning: Second compound - slight progression]   │ │
│  │                                                          │ │
│  │ B1. Incline Dumbbell Press (Superset)                  │ │
│  │     32kg × 10, 9, 8                                     │ │
│  │     Rest: 0:30 then immediately to B2                   │ │
│  │                                                          │ │
│  │ B2. Lateral Raises (Superset)                          │ │
│  │     12kg × 15, 14, 12                                   │ │
│  │     Rest: 2:00 after superset, then repeat              │ │
│  │     [Reasoning: Superset saves 6 minutes total]         │ │
│  │                                                          │ │
│  │ C. Tricep Pushdowns                                     │ │
│  │     32kg × 12, 12, 10                                   │ │
│  │     Rest: 1:30 between sets                             │ │
│  │     [Reasoning: Isolation - shorter rest adequate]      │ │
│  │                                                          │ │
│  │ ⏱️  Total time: ~58 minutes                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  💡 Training Notes:                                          │
│  • Focus on bar speed to maintain power output with shorter │
│    rest periods                                              │
│  • If feeling strong, add cable flyes as finisher (2 sets)  │
│  • Superset timing is tight - set up both stations before   │
│    starting                                                  │
│  • Next session: return to 3:00 rest if time allows for     │
│    better recovery                                           │
│                                                              │
│  [Start Workout Timer] [Export to Calendar] [Copy] [Close]  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## UI Implementation Details

### HTMX Version (Recommended)

**Benefits:**
- Zero JavaScript for basic interactions
- Partial page updates = fast, responsive feel
- Server-side rendering = simpler state management
- Easy to add progressive enhancement

**Key Features:**
```html
<!-- Exercise card with HTMX -->
<div class="exercise-card">
  <h3>Barbell Bench Press</h3>
  <div id="exercise-stats">...</div>
  
  <!-- LLM action triggers partial updates -->
  <button 
    hx-post="/api/exercise/1/analyze"
    hx-target="#llm-results"
    hx-indicator="#loading-spinner"
    hx-vals='{"context": "js:document.getElementById(\"context-input\").value"}'
  >
    Analyze Progression
  </button>
  
  <!-- Results container -->
  <div id="llm-results"></div>
  <div id="loading-spinner" class="htmx-indicator">
    Analyzing...
  </div>
</div>
```

**FastAPI Endpoint:**
```python
@app.post("/api/exercise/{exercise_id}/analyze")
async def analyze_exercise(
    exercise_id: int,
    context: str = "",
    weeks: int = 8
):
    # Fetch exercise data
    exercise_data = db.get_exercise_history(exercise_id, weeks)
    
    # Call LLM
    analysis = llm_client.analyze_progression(
        exercise_data=exercise_data,
        user_context=context
    )
    
    # Return HTML fragment
    return templates.TemplateResponse(
        "components/analysis_card.html",
        {"analysis": analysis}
    )
```

### Streamlit Version

**Benefits:**
- Extremely rapid prototyping
- Built-in state management
- Native charting components
- Python-only development

**Key Features:**
```python
import streamlit as st

# Sidebar navigation
with st.sidebar:
    st.title("🏋️ GymUp AI Trainer")
    page = st.radio("Navigate", ["Dashboard", "Programs", "Exercises", "Analytics"])

if page == "Exercises":
    # Exercise selector
    exercise = st.selectbox(
        "Select Exercise",
        db.get_all_exercises(),
        format_func=lambda x: x.name
    )
    
    # Stats display
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Est. 1RM", f"{exercise.one_rm_estimate}kg")
    with col2:
        st.metric("Last Session", f"{exercise.last_weight}kg × {exercise.last_reps}")
    # ... more stats
    
    # Progression chart
    st.plotly_chart(
        create_progression_chart(exercise.id),
        use_container_width=True
    )
    
    # LLM actions with context
    st.subheader("🤖 AI Analysis")
    user_context = st.text_area(
        "Additional Context (Optional)",
        placeholder="e.g., 'Shoulder pain resolved...'"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Analyze Progression"):
            with st.spinner("Analyzing with AI..."):
                analysis = llm.analyze_progression(
                    exercise_id=exercise.id,
                    context=user_context
                )
            st.success("Analysis Complete")
            with st.expander("View Analysis", expanded=True):
                st.markdown(analysis.summary)
                st.info("**Key Findings:**\n" + "\n".join(analysis.findings))
                st.warning("**Areas to Monitor:**\n" + "\n".join(analysis.warnings))
    
    with col2:
        if st.button("⚡ Suggest Next Weights"):
            with st.spinner("Generating recommendation..."):
                rec = llm.suggest_next_weights(
                    exercise_id=exercise.id,
                    context=user_context
                )
            st.success(f"Recommended: {rec.weight}kg")
            with st.expander("View Reasoning", expanded=True):
                st.markdown(rec.reasoning)
                st.code(rec.workout_plan, language="markdown")
```

## Visualization Examples

### Exercise Progression Chart (Plotly)
```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_progression_chart(exercise_id: int, weeks: int = 12):
    """Interactive chart showing weight, volume, and RPE trends"""
    
    workouts = db.get_exercise_history(exercise_id, weeks=weeks)
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=("Weight Progression", "Volume (Tonnage)", "RPE Trend"),
        row_heights=[0.4, 0.3, 0.3]
    )
    
    # Weight progression with rep ranges
    for set_num in [1, 2, 3]:
        weights = [w.sets[set_num-1].weight for w in workouts if len(w.sets) >= set_num]
        reps = [w.sets[set_num-1].reps for w in workouts if len(w.sets) >= set_num]
        dates = [w.date for w in workouts if len(w.sets) >= set_num]
        
        fig.add_trace(
            go.Scatter(
                x=dates, y=weights,
                mode='lines+markers',
                name=f'Set {set_num}',
                text=[f'{w}kg × {r}' for w, r in zip(weights, reps)],
                hovertemplate='<b>%{text}</b><br>%{x}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Volume trend
    tonnage = [sum(s.weight * s.reps for s in w.sets) for w in workouts]
    fig.add_trace(
        go.Bar(x=[w.date for w in workouts], y=tonnage, name='Tonnage'),
        row=2, col=1
    )
    
    # RPE trend
    avg_rpe = [sum(s.hard_sense for s in w.sets) / len(w.sets) for w in workouts]
    fig.add_trace(
        go.Scatter(
            x=[w.date for w in workouts], y=avg_rpe,
            mode='lines+markers',
            name='Avg RPE',
            line=dict(color='orange', width=3)
        ),
        row=3, col=1
    )
    
    fig.update_layout(
        height=800,
        showlegend=True,
        hovermode='x unified',
        template='plotly_dark'
    )
    
    return fig
```

### Program Heatmap (Muscle Group Volume)
```python
def create_muscle_volume_heatmap(program_id: int, weeks: int = 4):
    """Heatmap showing volume distribution across muscle groups"""
    
    data = db.get_program_muscle_volume(program_id, weeks)
    
    muscle_groups = ['Chest', 'Back', 'Shoulders', 'Biceps', 'Triceps', 'Quads', 'Hamstrings', 'Glutes']
    weeks_labels = [f'Week {i+1}' for i in range(weeks)]
    
    # Volume matrix (muscle_groups × weeks)
    volume_matrix = [[data[muscle][week] for week in range(weeks)] for muscle in muscle_groups]
    
    fig = go.Figure(data=go.Heatmap(
        z=volume_matrix,
        x=weeks_labels,
        y=muscle_groups,
        colorscale='Viridis',
        text=volume_matrix,
        texttemplate='%{text:.0f}kg',
        textfont={"size": 10},
        hovertemplate='<b>%{y}</b><br>%{x}: %{z:.0f}kg<extra></extra>'
    ))
    
    fig.update_layout(
        title='Muscle Group Volume Distribution',
        xaxis_title='Week',
        yaxis_title='Muscle Group',
        height=500
    )
    
    return fig
```

### 1RM Trajectory Prediction
```python
def create_1rm_prediction_chart(exercise_id: int, weeks_back: int = 12, weeks_forward: int = 4):
    """Show historical 1RM estimates with linear regression projection"""
    
    import numpy as np
    from scipy import stats
    
    workouts = db.get_exercise_history(exercise_id, weeks=weeks_back)
    
    # Calculate 1RM for each workout
    one_rms = [calculate_1rm(max(s.weight for s in w.sets), max(s.reps for s in w.sets)) 
               for w in workouts]
    dates = [w.date for w in workouts]
    
    # Linear regression
    x = np.arange(len(one_rms))
    slope, intercept, r_value, _, _ = stats.linregress(x, one_rms)
    
    # Projection
    future_x = np.arange(len(one_rms), len(one_rms) + weeks_forward * 2)  # 2 sessions/week
    projected = slope * future_x + intercept
    
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=dates, y=one_rms,
        mode='markers',
        name='Calculated 1RM',
        marker=dict(size=10, color='blue')
    ))
    
    # Regression line
    fig.add_trace(go.Scatter(
        x=dates + [dates[-1] + timedelta(weeks=weeks_forward)],
        y=[slope * i + intercept for i in range(len(one_rms) + weeks_forward * 2)],
        mode='lines',
        name=f'Trend (R²={r_value**2:.3f})',
        line=dict(color='green', dash='dash')
    ))
    
    # Projection
    projection_dates = [dates[-1] + timedelta(weeks=i/2) for i in range(1, weeks_forward*2 + 1)]
    fig.add_trace(go.Scatter(
        x=projection_dates, y=projected,
        mode='lines+markers',
        name='4-Week Projection',
        line=dict(color='orange', dash='dot'),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=f'1RM Trajectory & Projection',
        xaxis_title='Date',
        yaxis_title='Estimated 1RM (kg)',
        hovermode='x unified'
    )
    
    return fig
```

## Google Drive Integration

### Setup Instructions

1. **Enable Google Drive API:**
   ```bash
   # Install dependencies
   pip install PyDrive2 google-auth-oauthlib
   ```

2. **Get OAuth Credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create new project or select existing
   - Enable Google Drive API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download `credentials.json`
   - Save to `~/.gymup-tracker/gdrive_credentials.json`

3. **First-time Authentication:**
   ```bash
   gymup-tracker setup-gdrive
   # Opens browser for Google login
   # Saves refresh token for future use
   ```

### Usage

```bash
# Direct Google Drive URL
gymup-tracker start --db "https://drive.google.com/file/d/1ABC...XYZ/view"

# Or use file ID directly
gymup-tracker start --db-gdrive-id "1ABC...XYZ"

# Auto-sync mode (downloads on start, uploads on exit)
gymup-tracker start --db-gdrive-id "1ABC...XYZ" --gdrive-sync
```

### Implementation

```python
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

class GDriveManager:
    def __init__(self, credentials_path: str):
        self.gauth = GoogleAuth()
        self.gauth.LoadCredentialsFile(credentials_path)
        
        if self.gauth.credentials is None:
            self.gauth.LocalWebserverAuth()
        elif self.gauth.access_token_expired:
            self.gauth.Refresh()
        else:
            self.gauth.Authorize()
            
        self.gauth.SaveCredentialsFile(credentials_path)
        self.drive = GoogleDrive(self.gauth)
    
    def download_file(self, file_id: str, destination: str) -> str:
        """Download file from Google Drive"""
        file = self.drive.CreateFile({'id': file_id})
        file.GetContentFile(destination)
        return destination
    
    def upload_file(self, local_path: str, file_id: str = None) -> str:
        """Upload/update file to Google Drive"""
        if file_id:
            # Update existing file
            file = self.drive.CreateFile({'id': file_id})
        else:
            # Create new file
            file = self.drive.CreateFile({
                'title': os.path.basename(local_path)
            })
        
        file.SetContentFile(local_path)
        file.Upload()
        return file['id']
    
    def extract_file_id(self, url: str) -> str:
        """Extract file ID from Google Drive URL"""
        if '/file/d/' in url:
            return url.split('/file/d/')[1].split('/')[0]
        elif 'id=' in url:
            return url.split('id=')[1].split('&')[0]
        else:
            return url  # Assume it's already a file ID

# CLI integration
@click.command()
@click.option('--db', help='Database path or Google Drive URL')
@click.option('--gdrive-sync', is_flag=True, help='Auto-sync with Google Drive')
def start(db: str, gdrive_sync: bool):
    if 'drive.google.com' in db or db.startswith('1'):
        # Google Drive URL or file ID
        gdrive = GDriveManager('~/.gymup-tracker/gdrive_credentials.json')
        file_id = gdrive.extract_file_id(db)
        
        local_path = '~/.gymup-tracker/workout.db'
        print(f"📥 Downloading database from Google Drive...")
        gdrive.download_file(file_id, local_path)
        
        if gdrive_sync:
            # Register upload on exit
            import atexit
            atexit.register(lambda: gdrive.upload_file(local_path, file_id))
            print("🔄 Auto-sync enabled - will upload on exit")
        
        db_path = local_path
    else:
        db_path = db
    
    # Start app with local database
    start_server(db_path)
```

### Sync Strategies

**Option 1: Download-Only (Safe)**
- Downloads database on startup
- All changes stay local
- Manual upload when ready

**Option 2: Auto-Sync (Convenient)**
- Downloads on startup
- Uploads on clean exit
- Risk: concurrent modifications

**Option 3: Real-time Sync (Advanced)**
- Use Google Drive API file watching
- Detect external changes
- Merge or reload database
- Complexity: conflict resolution

**Recommended:** Start with Download-Only, add manual upload button in UI

## Additional LLM Use Cases

Beyond the core exercise and day-level functions, here are more opportunities where LLM assistance adds value:

### Smart Insights & Notifications

**11. `detect_injury_risk`**
- **Trigger**: Automatic when unusual patterns detected
- **Input**: Exercise ID, recent RPE spikes, volume jumps, failed sets
- **Output**: Risk assessment with preventive advice
- **Example**: "Squat volume increased 40% in 2 weeks + RPE 9-10 on all sets → overuse risk"
- **User Context**: "Knee feels tight after workouts"

**12. `interpret_training_session`**
- **Trigger**: Post-workout reflection
- **Input**: Completed workout data, user notes
- **Output**: Performance summary, recovery advice, adjustments for next session
- **Example**: "All pressing movements felt heavy despite adequate rest → may indicate systemic fatigue"
- **User Context**: "Felt unusually tired throughout workout"

**13. `compare_exercise_performance`**
- **Trigger**: User selects 2+ exercises to compare
- **Input**: Multiple exercise IDs, time period
- **Output**: Comparative analysis of progression rates, volume ratios
- **Example**: "Bench press progressing well (+8% in 4 weeks) but overhead press stalled → check shoulder mobility"
- **User Context**: "Want to bring up shoulders"

### Program Design Assistance

**14. `suggest_program_modification`**
- **Trigger**: User wants to adjust existing program
- **Input**: Program ID, modification goal (strength, hypertrophy, cut, etc.)
- **Output**: Specific exercise/set/rep adjustments
- **Example**: "To emphasize hypertrophy, increase volume on isolation movements by 25%, reduce intensity 5-10%"
- **User Context**: "Switching focus to muscle building after strength phase"

**15. `design_deload_protocol`**
- **Input**: Program ID, fatigue level, deload preference
- **Output**: Week-by-week deload plan
- **Example**: "Reduce volume to 50% week 1, maintain intensity; return to 75% volume week 2"
- **User Context**: "Prefer active recovery over complete rest"

**16. `periodization_planner`**
- **Input**: Program ID, training goals, timeline (12-16 weeks)
- **Output**: Phase-by-phase plan (accumulation, intensification, peaking, deload)
- **Example**: "Weeks 1-4: volume accumulation, Weeks 5-8: intensity focus, Week 9: deload, Weeks 10-12: peaking"
- **User Context**: "Preparing for powerlifting meet in 3 months"

### Recovery & Adaptation Analysis

**17. `analyze_recovery_patterns`**
- **Input**: Program ID, RPE data, rest day frequency
- **Output**: Recovery adequacy assessment
- **Example**: "RPE consistently increases across weeks without drop → insufficient recovery between sessions"
- **User Context**: "Sleep only 6 hours/night lately"

**18. `suggest_rest_day_placement`**
- **Input**: Program structure, muscle group overlap, typical weekly schedule
- **Output**: Optimal rest day positioning
- **Example**: "Move rest day between Leg Day and Pull Day to avoid back fatigue affecting deadlifts"
- **User Context**: "Weekends work best for rest days"

### Technique & Form Guidance

**19. `form_check_reminder`**
- **Input**: Exercise ID, weight jump, rep quality decline
- **Output**: Form breakdown likelihood with cues
- **Example**: "Weight increased 10kg but reps dropped from 8→5 → possible form compromise. Focus on: tempo, depth, bar path"
- **User Context**: "Bar feels like it's drifting forward on descent"

**20. `suggest_warmup_protocol`**
- **Input**: Exercise ID, working weight, user mobility notes
- **Output**: Specific warmup sets with weights/reps/mobility work
- **Example**: "For 100kg squat: 20kg×10, 40kg×8, 60kg×5, 80kg×3 + hip flexor stretch, ankle mobility"
- **User Context**: "Tight hip flexors, need extra warmup"

### Data Interpretation

**21. `explain_metric_change`**
- **Input**: Metric name (tonnage, 1RM, volume), time period, change direction
- **Output**: Plain-language explanation of what it means
- **Example**: "Tonnage increased 15% but 1RM unchanged → improved work capacity without strength gains, good for hypertrophy phase"
- **User Context**: "Not sure if I'm making progress"

**22. `nutrition_training_correlation`** *(if nutrition data available)*
- **Input**: Workout performance, calorie/protein intake
- **Output**: Correlation analysis
- **Example**: "Performance dips on days with <150g protein → consider increasing protein on training days"
- **User Context**: "Cutting calories to lose weight"

### Motivational & Educational

**23. `celebrate_milestones`**
- **Input**: Recent PRs, consistency streaks, volume landmarks
- **Output**: Encouraging message with context
- **Example**: "New PR on deadlift! This is a 12.5% increase from 3 months ago. Your progression is ahead of typical intermediate lifter curves."

**24. `educational_insights`**
- **Input**: Exercise ID or training principle question
- **Output**: Science-backed explanation
- **Example**: "Why does bench press respond well to varied rep ranges? Explanation of muscle fiber recruitment, time under tension, metabolic stress..."
- **User Context**: "Want to understand the science behind my programming"

### Export & Sharing

**25. `generate_workout_summary`**
- **Input**: Training session ID
- **Output**: Shareable workout recap (text/PDF)
- **Example**: "Push Day - Jan 27, 2026: Hit new bench PR (85kg×5), total volume 5,240kg. Key highlight: Improved bar speed on final set."

**26. `create_progress_report`**
- **Input**: Time period (monthly, quarterly)
- **Output**: Comprehensive progress document
- **Example**: PDF with charts, PRs, volume trends, LLM analysis of overall progression

## Advanced Features

### Adaptive Learning System

**Feedback Loop:**
1. LLM suggests next weight (e.g., 82.5kg × 8)
2. User performs workout, logs actual performance (e.g., 82.5kg × 8, 8, 7)
3. System compares prediction accuracy
4. Adjust LLM prompts or rule-based fallback weights

**Implementation:**
```python
class AdaptiveLearning:
    def track_recommendation(self, recommendation_id, predicted, actual):
        """Store recommendation and outcome"""
        self.db.save_recommendation_outcome(
            id=recommendation_id,
            predicted_weight=predicted.weight,
            predicted_reps=predicted.reps,
            actual_weight=actual.weight,
            actual_reps=actual.reps,
            accuracy_score=self.calculate_accuracy(predicted, actual)
        )
    
    def calculate_accuracy(self, predicted, actual):
        """Score: 1.0 = perfect, <0.8 = needs adjustment"""
        weight_diff = abs(predicted.weight - actual.weight) / predicted.weight
        rep_diff = abs(predicted.reps - actual.reps) / predicted.reps
        return 1.0 - (weight_diff + rep_diff) / 2
    
    def adjust_future_prompts(self, exercise_id):
        """Personalize prompts based on past accuracy"""
        stats = self.db.get_recommendation_stats(exercise_id)
        
        if stats.avg_accuracy < 0.8:
            if stats.avg_under_prediction:
                return "User tends to exceed predictions - be slightly more aggressive"
            else:
                return "User struggles with predictions - be more conservative"
        return ""
```

### Integration Possibilities

**Fitness Trackers:**
- **Garmin/Apple Watch**: HRV, resting heart rate → recovery readiness score
- **Whoop/Oura Ring**: Sleep quality, strain → adjust workout intensity
- **Implementation**: Webhook endpoints, periodic polling, manual CSV import

**Nutrition Tracking:**
- **MyFitnessPal API**: Calorie/macro data → context for performance analysis
- **LLM Insight**: "Low performance correlates with <2000 cal days during cut"

**Calendar Integration:**
- **Google Calendar**: Detect high-stress periods, travel, rest days
- **LLM Adjustment**: "Business trip next week → suggest bodyweight alternative exercises"

**External Databases:**
- **ExRx.net API**: Exercise library, biomechanics info
- **PubMed API**: Fetch relevant exercise science research
- **LLM Enhancement**: Ground recommendations in scientific literature

### Multi-User Features

The database already supports `user_id` field, enabling:

**Shared Programs:**
- Coach creates program template
- Multiple users follow same structure
- Individual progression tracking
- Comparative analytics (anonymized)

**Team/Group Features:**
- Leaderboards (total tonnage, PR counts)
- Group challenges
- Shared workout plans
- Social motivation

**Implementation:**
```python
class MultiUserSupport:
    def create_shared_program(self, coach_id, program_template):
        """Coach creates program that users can clone"""
        program = self.db.create_program(
            user_id=coach_id,
            is_template=True,
            **program_template
        )
        return program
    
    def clone_program_for_user(self, user_id, template_id):
        """User copies template with personal tracking"""
        template = self.db.get_program(template_id)
        return self.db.create_program(
            user_id=user_id,
            source_template_id=template_id,
            **template.to_dict()
        )
    
    def get_leaderboard(self, metric='total_tonnage', period='month'):
        """Anonymous comparison across users"""
        return self.db.query_aggregate(
            metric=metric,
            period=period,
            anonymize=True
        )
```

### Privacy & Security Enhancements

**Data Encryption:**
- Encrypt database at rest (SQLCipher)
- Password-protected backups
- Secure credential storage (keyring library)

**LLM Privacy:**
- All processing on local machine
- No external API calls (except optional OpenAI fallback with user consent)
- User data never leaves device

**Export Controls:**
- Watermark shared reports
- Option to exclude sensitive metrics from exports
- Anonymization for social sharing

## Performance Considerations

### Database Optimization
- Add indexes on frequently queried columns (`training.startDateTime`, `workout.th_exercise_id`)
- Use prepared statements for repeated queries
- Implement query result caching for static data (exercise templates)
- Batch inserts for bulk operations

### LLM Inference
- **Cold start**: ~2-5 seconds for model loading (mitigate with keep-alive)
- **Warm inference**: <1 second for 7B models, 2-4 seconds for 13B+ models
- **Batch processing**: Process full program recommendations in single pass
- **Caching strategy**: Hash-based caching of LLM responses (90%+ hit rate for stable workouts)

### Scalability
- SQLite suitable for single-user, local deployment
- For multi-user web app: migrate to PostgreSQL
- Redis for LLM response caching in production
- Background job queue (Celery) for bulk recommendation generation

## Testing Strategy

### Unit Tests
```python
# test_analytics.py
def test_one_rm_calculation():
    assert calculate_1rm(100, 5) == pytest.approx(115, rel=0.02)

def test_plateau_detection():
    weights = [80, 80, 80, 80, 80]
    dates = [date.today() - timedelta(weeks=i) for i in range(5)]
    assert detect_plateau(weights, dates, threshold_weeks=2) == True

# test_llm_integration.py
@patch('requests.post')
def test_llm_recommendation_parsing(mock_post):
    mock_response = {...}
    mock_post.return_value = Mock(json=lambda: mock_response)
    
    rec = engine.recommend_weight(exercise_id=1)
    assert rec.weight > 0
    assert rec.confidence in ['low', 'medium', 'high']
```

### Integration Tests
- End-to-end workflow: database → analysis → LLM → recommendation
- LLM availability fallback to rule-based system
- Database migration scenarios

### User Acceptance Testing
- Manual validation of recommendations against actual performance
- A/B testing: LLM vs rule-based recommendations
- Feedback collection mechanism

## Security & Privacy

### Data Handling
- **Local-first**: Database stays on user's machine
- **No telemetry**: No workout data sent to external services
- **LLM privacy**: Locally-hosted models = zero data leakage
- **Backup strategy**: Automated encrypted backups to user-controlled storage

### API Security
- LLM endpoint authentication if exposed over network
- Input validation to prevent prompt injection
- Rate limiting to prevent abuse
- Secrets management for any API keys (e.g., Garmin integration)

## Troubleshooting

### Common Issues

**LLM not responding**
```bash
# Check LLM server status
curl http://localhost:1234/v1/models

# Verify model loaded
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral-7b-instruct", "messages": [{"role": "user", "content": "test"}]}'
```

**Database locked errors**
- Ensure only one process accessing database
- Use `PRAGMA journal_mode=WAL` for better concurrency
- Check file permissions

**Inconsistent recommendations**
- Lower LLM temperature (0.2-0.3)
- Increase context window (more workout history)
- Validate input data quality (check for outliers)

## Contributing

We welcome contributions! Areas of focus:
- Additional analytics algorithms (velocity-based training, autoregulation)
- UI/UX improvements
- Prompt engineering optimizations
- Integration with other fitness platforms
- Internationalization (Dutch, Russian language support)

## License

MIT License - See LICENSE file for details

## Acknowledgments

- GymUp app for excellent workout tracking
- Open source LLM community (Mistral, Meta, Microsoft)
- Fitness science research informing recommendation algorithms

## Contact & Support

- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for feature requests
- **Email**: [your-email@example.com]

---

**Note**: This project is for personal fitness tracking and should not replace professional coaching. Always consult a qualified trainer for personalized programming, especially for complex movements or when recovering from injury.
