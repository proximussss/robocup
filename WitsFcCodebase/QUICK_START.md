# Quick Start Guide - Soccer AI

## 🚀 Getting Started

### Prerequisites
- Python 3.x installed
- RoboCup Soccer Simulator Server installed
- All dependencies from codebase

### Run Your Team

#### Option 1: Quick Start (Recommended)
```bash
# Linux/Mac
./start.sh

# Windows
python Run_Player.py
```

#### Option 2: Against Another Team
```bash
python Run_Two_Teams.py
```

#### Option 3: Debug Mode (with visualizations)
```bash
./start_debug.sh
```

---

## 📋 What Each File Does

### Main Decision Logic
**`agent/Agent.py`** - The brain of each player
- `select_skill()` - Main decision function (YOU DON'T NEED TO MODIFY THIS)
- Returns either `move()` or `kickTarget()` every cycle

### Strategy Components
**`strategy/Assignment.py`** - Role assignment (Submission 1)
- Uses Gale-Shapley algorithm
- Assigns players to optimal positions

**`strategy/DecisionMaker.py`** - Tactical intelligence
- "Should I pass?" 
- "Who's the best pass target?"
- "Am I under pressure?"

**`strategy/TacticalStrategies.py`** - Player behaviors
- What to do when I have the ball
- What to do when teammate has the ball
- Role-specific behaviors (goalkeeper, defender, etc.)

**`strategy/GameModeHandler.py`** - Game mode management
- Handles kickoffs, free kicks, corners, etc.

### Formation System
**`formation/DynamicFormation.py`** - Smart formations
- Formations adapt to ball position
- Different formations for attack/defense/set pieces

**`formation/Formation.py`** - Static formations
- Backup formations if needed

---

## 🎮 How It Plays

### The Decision Flow (Simple Version)
```
1. Where's the ball? → Generate smart formation
2. Who's closest? → That player is "active"
3. Active player:
   - Under pressure? → Pass
   - Close to goal? → Shoot
   - Have space? → Dribble
4. Other players: → Move to formation position
```

### Example Scenarios

**Scenario: Our kickoff**
```
All players: Move to kickoff formation
Formation ready? → Active player kicks toward goal
```

**Scenario: Ball in midfield, I'm closest**
```
Opponent nearby? → Yes → Find teammate → Pass
                   No  → Dribble toward goal
```

**Scenario: Ball in midfield, teammate closer**
```
What's my role? → Defender → Stay back, mark space
                → Midfielder → Support the play
                → Forward → Get ready for pass
```

---

## 🎯 Key Features

### ✅ Stable Role Assignment
Uses Gale-Shapley algorithm to assign players to positions optimally.
No two players will want to swap positions.

### ✅ Dynamic Formations
- Ball in our half? → Defensive formation
- Ball in their half? → Attacking formation
- Ball in midfield? → Balanced formation

### ✅ Smart Passing
Evaluates teammates and only passes when:
- Under pressure from opponent
- Teammate is in better position
- Forward pass available

### ✅ Role-Based Behavior
Each player acts according to their position:
- **Goalkeeper**: Stays near goal, tracks ball
- **Defenders**: Mark opponents, cover defensive area
- **Midfielders**: Support both attack and defense
- **Forwards**: Position for passes, attack goal

### ✅ All Game Modes Supported
- Kickoff (left/right)
- Play on (active game)
- Free kicks
- Corner kicks
- Goal kicks
- Kick-ins

---

## 🔧 Customization Tips

### Want More Aggressive Play?
Edit `strategy/TacticalStrategies.py`:
```python
# Line ~30: Change passing threshold
if self.strategy.min_opponent_ball_dist < 2.0:  # Was 1.5
    return True  # Pass
```

### Want Different Formation?
Edit `formation/DynamicFormation.py`:
```python
# Adjust formation positions in _dynamic_play_formation()
defense_x = -8  # Was -9 (more attacking)
```

### Want More Shooting?
Edit `strategy/TacticalStrategies.py`:
```python
# Line ~55: Change shooting distance
if dist_to_goal < 10:  # Was 8 (shoot from further)
    shoot_target = goal_pos
```

---

## 🐛 Troubleshooting

### Players Keep Falling
**Cause**: Code is taking too long to execute
**Solution**: Reduce complexity or check for infinite loops

### Players Don't Move
**Cause**: Not returning move() or kickTarget()
**Solution**: Check select_skill() always returns an action

### Team Doesn't Attack
**Cause**: Formation too defensive
**Solution**: Adjust formation positions in DynamicFormation.py

### Multiple Players Chase Ball
**Cause**: Role assignment not working
**Solution**: Verify Assignment.py is being called correctly

---

## 📊 Tournament Strategy

### Swiss Tournament Tips
1. **Consistency**: The AI plays consistently (good!)
2. **Adaptation**: Formations adapt to ball position
3. **No Timeouts**: Efficient code prevents falls
4. **Team Coordination**: Stable role assignment prevents clustering

### What Makes This Competitive
- ✅ Optimal role assignment (Gale-Shapley)
- ✅ Adaptive strategy (formations change)
- ✅ Smart decisions (pass vs shoot vs dribble)
- ✅ Robust (handles all game modes)
- ✅ Fast (no performance issues)

---

## 📁 File Structure Quick Reference

```
WitsFcCodebase/
├── agent/
│   └── Agent.py              ← Main decision logic (select_skill)
├── strategy/
│   ├── Assignment.py         ← Submission 1 (Gale-Shapley)
│   ├── Strategy.py           ← Game state data
│   ├── GameModeHandler.py    ← Handles different game modes
│   ├── DecisionMaker.py      ← "Should I pass?" logic
│   └── TacticalStrategies.py ← Attack/defend behaviors
├── formation/
│   ├── Formation.py          ← Static formations
│   └── DynamicFormation.py   ← Adaptive formations
└── Documentation/
    ├── SOCCER_AI_DOCUMENTATION.md   ← Detailed docs
    ├── IMPLEMENTATION_SUMMARY.md    ← What was built
    └── QUICK_START.md              ← This file
```

---

## 🎓 Understanding the Code

### The Main Function: `select_skill()`
Location: `agent/Agent.py` (line ~217)

This function is called every game cycle and must return either:
- `self.move(target, orientation)` - Walk to a position
- `self.kickTarget(strategyData, mypos, target)` - Kick the ball

### The Flow:
```python
def select_skill(self, strategyData):
    # 1. What game mode? (kickoff, play on, free kick, etc.)
    game_mode = determine_game_mode()
    
    # 2. Generate formation based on ball position
    formation = create_dynamic_formation()
    
    # 3. Assign players to formation positions
    assignments = role_assignment()
    
    # 4. Am I closest to ball?
    if am_closest:
        # Attack: pass, shoot, or dribble
        return attack_action()
    else:
        # Support: move to formation position
        return move_to_position()
```

---

## 💡 Pro Tips

1. **Test Small Changes**: Modify one thing at a time
2. **Use Visualizations**: Run with `enable_draw=True` to see formations
3. **Watch Replays**: Use RoboViz to analyze gameplay
4. **Check Logs**: Enable logging to debug issues
5. **Compare Teams**: Run against other teams to find weaknesses

---

## ✅ Checklist Before Tournament

- [ ] Team runs without errors
- [ ] Players don't fall frequently
- [ ] Team attacks the correct goal
- [ ] Goalkeeper stays near goal
- [ ] Players maintain formation
- [ ] Team responds to set pieces
- [ ] All 5 players active and moving

---

## 🎉 You're Ready!

Your team is now equipped with:
- **Stable role assignment** (Submission 1) ✅
- **Complete soccer AI** (Submission 2) ✅
- **Dynamic formations** ✅
- **Smart decision making** ✅
- **Tournament-ready code** ✅

Good luck in the tournament! 🏆

---

## Need Help?

1. Check `SOCCER_AI_DOCUMENTATION.md` for detailed explanations
2. Check `IMPLEMENTATION_SUMMARY.md` for component overview
3. Review code comments in each file
4. Test individual components in isolation

**Remember**: The AI makes decisions every 20ms. Keep it simple and fast!

