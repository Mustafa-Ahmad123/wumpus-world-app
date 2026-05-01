import streamlit as st
import random
import json
from logic_engine import WumpusKB, ResolutionEngine

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wumpus Logic Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Share Tech Mono', monospace;
}

.stApp {
    background: #0a0e1a;
    color: #c8deff;
}

h1, h2, h3 {
    font-family: 'Orbitron', monospace !important;
    color: #00c8ff !important;
    letter-spacing: 3px;
    text-shadow: 0 0 20px rgba(0,200,255,0.4);
}

.main-title {
    font-family: 'Orbitron', monospace;
    font-size: 2rem;
    color: #00c8ff;
    text-align: center;
    letter-spacing: 6px;
    text-shadow: 0 0 30px rgba(0,200,255,0.6);
    margin-bottom: 4px;
}
.subtitle {
    text-align: center;
    color: #3a6080;
    font-size: 0.75rem;
    letter-spacing: 3px;
    margin-bottom: 20px;
}

/* Grid cells */
.cell-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
}

.grid-cell {
    width: 80px; height: 80px;
    border-radius: 6px;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    font-size: 1.6rem;
    border: 2px solid;
    position: relative;
    cursor: pointer;
    transition: all 0.2s;
    font-family: 'Share Tech Mono', monospace;
}

.cell-agent   { background: rgba(0,200,255,0.18); border-color: #00c8ff; }
.cell-visited { background: #1a2a3a; border-color: #2a4a6a; }
.cell-safe    { background: rgba(0,255,136,0.12); border-color: #00ff88; }
.cell-danger  { background: rgba(255,51,85,0.18); border-color: #ff3355; }
.cell-unknown { background: #1a2535; border-color: #1e3a5f; }
.cell-pit-rev { background: rgba(255,51,85,0.35); border-color: #ff3355; }
.cell-wumpus-rev { background: rgba(255,100,0,0.3); border-color: #ff6400; }
.cell-gold-rev { background: rgba(255,215,0,0.2); border-color: #ffd700; }

.coord-label {
    position: absolute; top: 3px; left: 5px;
    font-size: 0.5rem; color: #3a5a7a;
    font-family: 'Share Tech Mono', monospace;
}
.cell-sublabel {
    font-size: 0.5rem; color: #5a8aaa;
    letter-spacing: 1px; font-family: 'Share Tech Mono', monospace;
}

/* Metric cards */
.metric-card {
    background: #0f1626;
    border: 1px solid #1e3a5f;
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.metric-label { font-size: 0.65rem; color: #5a7a9a; letter-spacing: 2px; }
.metric-value {
    font-family: 'Orbitron', monospace;
    font-size: 1.4rem; color: #00c8ff;
}

/* Status bar */
.status-playing { background: rgba(0,200,255,0.1); border: 1px solid #1e3a5f; color: #00c8ff; border-radius:4px; padding:8px 14px; font-size:0.8rem; text-align:center; }
.status-win     { background: rgba(0,255,136,0.15); border: 1px solid #00ff88; color: #00ff88; border-radius:4px; padding:8px 14px; font-size:0.8rem; text-align:center; }
.status-dead    { background: rgba(255,51,85,0.18); border: 1px solid #ff3355; color: #ff3355; border-radius:4px; padding:8px 14px; font-size:0.8rem; text-align:center; }

/* Log boxes */
.log-box {
    background: #070c16;
    border: 1px solid #1e3a5f;
    border-radius: 4px;
    padding: 10px;
    max-height: 220px;
    overflow-y: auto;
    font-size: 0.65rem;
    line-height: 1.9;
    font-family: 'Share Tech Mono', monospace;
}
.log-new       { color: #00c8ff; }
.log-resolve   { color: #00ff88; }
.log-contradict{ color: #ff3355; }
.log-neutral   { color: #4a7a9a; }
.log-warn      { color: #ffaa00; }

/* Percept tags */
.percept-tag {
    display: inline-block;
    padding: 4px 10px;
    border-left: 3px solid #00c8ff;
    background: rgba(0,200,255,0.07);
    border-radius: 2px;
    margin: 3px 0;
    font-size: 0.75rem;
    color: #c8deff;
}

/* Panel headers */
.panel-header {
    font-family: 'Orbitron', monospace;
    font-size: 0.62rem;
    letter-spacing: 3px;
    color: #00c8ff;
    border-bottom: 1px solid #1e3a5f;
    padding-bottom: 6px;
    margin-bottom: 10px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0f1626 !important;
    border-right: 1px solid #1e3a5f;
}
</style>
""", unsafe_allow_html=True)


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def key(r, c): return f"{r},{c}"

def get_adj(r, c, rows, cols):
    return [(ar, ac) for ar, ac in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]
            if 0 <= ar < rows and 0 <= ac < cols]

def shuffle(lst):
    lst2 = lst[:]
    random.shuffle(lst2)
    return lst2


# ─── WORLD GENERATOR ─────────────────────────────────────────────────────────
def generate_world(rows, cols, num_pits):
    grid = [[{"pit":False,"wumpus":False,"gold":False,"breeze":False,"stench":False}
              for _ in range(cols)] for _ in range(rows)]

    cells = [(r, c) for r in range(rows) for c in range(cols)
             if not (r == rows-1 and c == 0)]
    cells = shuffle(cells)

    num_pits = min(num_pits, len(cells) - 2)
    for i in range(num_pits):
        grid[cells[i][0]][cells[i][1]]["pit"] = True

    non_pit = [(r,c) for r,c in cells if not grid[r][c]["pit"]]
    non_pit = shuffle(non_pit)
    wr, wc = non_pit[0]
    grid[wr][wc]["wumpus"] = True

    gold_pool = [(r,c) for r,c in non_pit if not (r==wr and c==wc)]
    gold_pool = shuffle(gold_pool)
    gr, gc = gold_pool[0]
    grid[gr][gc]["gold"] = True

    # Percept propagation
    for r in range(rows):
        for c in range(cols):
            for ar, ac in get_adj(r, c, rows, cols):
                if grid[r][c]["pit"]:   grid[ar][ac]["breeze"] = True
                if grid[r][c]["wumpus"]:grid[ar][ac]["stench"] = True

    return grid


# ─── SESSION STATE INIT ───────────────────────────────────────────────────────
def init_state():
    rows = st.session_state.get("cfg_rows", 4)
    cols = st.session_state.get("cfg_cols", 4)
    pits = st.session_state.get("cfg_pits", 3)

    grid = generate_world(rows, cols, pits)
    kb = WumpusKB(rows, cols)
    engine = ResolutionEngine(kb)

    st.session_state.grid = grid
    st.session_state.rows = rows
    st.session_state.cols = cols
    st.session_state.agent_r = rows - 1
    st.session_state.agent_c = 0
    st.session_state.visited = set()
    st.session_state.safe_cells = set()
    st.session_state.danger_cells = set()
    st.session_state.kb = kb
    st.session_state.engine = engine
    st.session_state.inf_steps = 0
    st.session_state.game_over = False
    st.session_state.revealed = False
    st.session_state.kb_log = []
    st.session_state.inf_log = []
    st.session_state.current_percepts = []
    st.session_state.status = ("AWAITING FIRST MOVE...", "playing")
    st.session_state.initialized = True

    # Enter start cell
    enter_cell(rows - 1, 0)


def add_kb_log(msg, cls="log-neutral"):
    st.session_state.kb_log.append((msg, cls))

def add_inf_log(msg, cls="log-neutral"):
    st.session_state.inf_log.append((msg, cls))


# ─── ENTER CELL LOGIC ────────────────────────────────────────────────────────
def enter_cell(r, c):
    s = st.session_state
    rows, cols = s.rows, s.cols
    grid = s.grid
    cell = grid[r][c]
    disp = f"[{rows - r},{c + 1}]"

    s.visited.add(key(r, c))
    s.safe_cells.add(key(r, c))

    # Death checks
    if cell["pit"]:
        s.status = ("💀 AGENT FELL INTO A PIT! GAME OVER.", "dead")
        s.game_over = True
        s.revealed = True
        return
    if cell["wumpus"]:
        s.status = ("💀 EATEN BY THE WUMPUS! GAME OVER.", "dead")
        s.game_over = True
        s.revealed = True
        return
    if cell["gold"]:
        s.status = ("🏆 GOLD FOUND! MISSION COMPLETE!", "win")
        s.game_over = True

    # Build percept list
    percepts = []
    if cell["breeze"]: percepts.append("💨 BREEZE")
    if cell["stench"]: percepts.append("💀 STENCH")
    if cell["gold"]:   percepts.append("✨ GLITTER")
    s.current_percepts = percepts

    # TELL KB
    add_kb_log(f"VISIT {disp}:", "log-new")
    if cell["breeze"]:
        add_kb_log(f"  TELL: B_{rows-r},{c+1} (Breeze)", "log-new")
        s.kb.tell_breeze(r, c)
    else:
        add_kb_log(f"  TELL: ¬B_{rows-r},{c+1} (No Breeze)", "log-new")
        s.kb.tell_no_breeze(r, c)

    if cell["stench"]:
        add_kb_log(f"  TELL: S_{rows-r},{c+1} (Stench)", "log-new")
        s.kb.tell_stench(r, c)
    else:
        add_kb_log(f"  TELL: ¬S_{rows-r},{c+1} (No Stench)", "log-new")
        s.kb.tell_no_stench(r, c)

    adj = get_adj(r, c, rows, cols)

    if not cell["breeze"]:
        for ar, ac in adj:
            if key(ar, ac) not in s.visited:
                s.kb.add_clause([f"NEG_P_{ar}_{ac}"])
                s.safe_cells.add(key(ar, ac))
                add_kb_log(f"  INFER: ¬P_{rows-ar},{ac+1} (no breeze→safe)", "log-resolve")
    else:
        clause = [f"P_{ar}_{ac}" for ar, ac in adj]
        s.kb.add_clause(clause)
        parts = " ∨ ".join(f"P_{rows-ar},{ac+1}" for ar,ac in adj)
        add_kb_log(f"  TELL: {parts} (breeze→pit nearby)", "log-warn")

    if not cell["stench"]:
        for ar, ac in adj:
            if key(ar, ac) not in s.visited:
                s.kb.add_clause([f"NEG_W_{ar}_{ac}"])
                add_kb_log(f"  INFER: ¬W_{rows-ar},{ac+1} (no stench→safe)", "log-resolve")

    # Run inference on unvisited neighbors
    run_inference()

    if not s.game_over:
        s.status = (f"Agent at {disp}. Exploring...", "playing")


def run_inference():
    s = st.session_state
    rows = s.rows
    for ar, ac in get_adj(s.agent_r, s.agent_c, rows, s.cols):
        if key(ar, ac) in s.visited:
            continue
        ck = key(ar, ac)
        disp = f"[{rows-ar},{ac+1}]"

        steps_before = s.engine.steps
        pit_safe   = s.engine.resolution_refutation(f"P_{ar}_{ac}")
        wump_safe  = s.engine.resolution_refutation(f"W_{ar}_{ac}")
        s.inf_steps += s.engine.steps - steps_before

        if pit_safe and wump_safe:
            s.safe_cells.add(ck)
            add_inf_log(f"✓ SAFE: {disp} — ¬P ∧ ¬W proved", "log-resolve")
        else:
            steps_before = s.engine.steps
            pit_danger  = s.engine.resolution_refutation(f"NEG_P_{ar}_{ac}")
            wump_danger = s.engine.resolution_refutation(f"NEG_W_{ar}_{ac}")
            s.inf_steps += s.engine.steps - steps_before
            if pit_danger or wump_danger:
                s.danger_cells.add(ck)
                add_inf_log(f"✗ DANGER: {disp} — hazard deduced", "log-contradict")
            else:
                add_inf_log(f"? UNKNOWN: {disp} — insufficient info", "log-neutral")


def move_agent(r, c):
    s = st.session_state
    if s.game_over:
        return
    if abs(r - s.agent_r) + abs(c - s.agent_c) != 1:
        s.status = ("⚠ Can only move to adjacent cells.", "playing")
        return
    s.agent_r = r
    s.agent_c = c
    enter_cell(r, c)


def auto_step():
    s = st.session_state
    if s.game_over:
        return
    rows, cols = s.rows, s.cols
    adj = get_adj(s.agent_r, s.agent_c, rows, cols)
    target = next(((r,c) for r,c in adj
                   if key(r,c) in s.safe_cells and key(r,c) not in s.visited), None)
    if not target:
        target = next(((r,c) for r,c in adj
                       if key(r,c) not in s.visited and key(r,c) not in s.danger_cells), None)
    if not target:
        target = next(((r,c) for r,c in adj if key(r,c) in s.visited), None)
    if target:
        s.agent_r, s.agent_c = target
        enter_cell(target[0], target[1])
    else:
        s.status = ("No moves available.", "playing")


# ─── GRID RENDERER ────────────────────────────────────────────────────────────
def render_grid():
    s = st.session_state
    rows, cols = s.rows, s.cols
    grid = s.grid
    revealed = s.revealed

    # Build HTML grid
    html = f"""<div style="display:grid;grid-template-columns:repeat({cols},88px);gap:4px;justify-content:center;padding:10px 0;">"""

    for r in range(rows):
        for c in range(cols):
            cell = grid[r][c]
            ck = key(r, c)
            is_agent   = (r == s.agent_r and c == s.agent_c)
            is_visited = ck in s.visited
            is_safe    = ck in s.safe_cells and not is_visited and not is_agent
            is_danger  = ck in s.danger_cells and not is_visited and not is_agent

            icon = ""
            label = ""
            percept_str = ""

            if is_agent:
                css_class = "cell-agent"
                icon = "🤖"
                label = "AGENT"
            elif revealed or is_visited:
                if cell["pit"]:
                    css_class = "cell-pit-rev"
                    icon = "🕳"
                    label = "PIT"
                elif cell["wumpus"]:
                    css_class = "cell-wumpus-rev"
                    icon = "👾"
                    label = "WUMPUS"
                elif cell["gold"]:
                    css_class = "cell-gold-rev"
                    icon = "💰"
                    label = "GOLD"
                else:
                    css_class = "cell-visited" if is_visited else "cell-safe"
                    icon = "✓"
                    label = "SAFE"
                if is_visited:
                    p = []
                    if cell["breeze"]: p.append("💨")
                    if cell["stench"]: p.append("💀")
                    percept_str = "".join(p)
            elif is_safe:
                css_class = "cell-safe"
                icon = "✓"
                label = "SAFE"
            elif is_danger:
                css_class = "cell-danger"
                icon = "⚠"
                label = "DANGER"
            else:
                css_class = "cell-unknown"
                icon = "?"
                label = ""

            coord = f"{rows - r},{c + 1}"
            cell_styles = {
                "cell-agent":      "background:rgba(0,200,255,0.18);border-color:#00c8ff;",
                "cell-visited":    "background:#1a2a3a;border-color:#2a4a6a;",
                "cell-safe":       "background:rgba(0,255,136,0.12);border-color:#00ff88;",
                "cell-danger":     "background:rgba(255,51,85,0.18);border-color:#ff3355;",
                "cell-unknown":    "background:#1a2535;border-color:#1e3a5f;",
                "cell-pit-rev":    "background:rgba(255,51,85,0.35);border-color:#ff3355;",
                "cell-wumpus-rev": "background:rgba(255,100,0,0.3);border-color:#ff6400;",
                "cell-gold-rev":   "background:rgba(255,215,0,0.2);border-color:#ffd700;",
            }
            extra = cell_styles.get(css_class, "background:#1a2535;border-color:#1e3a5f;")
            base = "width:80px;height:80px;position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;border-radius:6px;border:2px solid;font-family:'Share Tech Mono',monospace;"
            html += f'<div style="{base}{extra}"><span style="position:absolute;top:3px;left:5px;font-size:0.5rem;color:#3a5a7a;">{coord}</span><span style="font-size:1.5rem;line-height:1">{icon}</span><span style="font-size:0.5rem;color:#5a8aaa;letter-spacing:1px;">{label}</span><span style="font-size:0.6rem;color:#ffaa00">{percept_str}</span></div>'

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ─── MAIN UI ─────────────────────────────────────────────────────────────────
def main():
    # Title
    st.markdown('<div class="main-title">WUMPUS LOGIC AGENT</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">KNOWLEDGE-BASED PROPOSITIONAL INFERENCE ENGINE</div>', unsafe_allow_html=True)

    # ── Sidebar config ──
    with st.sidebar:
        st.markdown('<div class="panel-header">⚙ ENVIRONMENT CONFIG</div>', unsafe_allow_html=True)
        rows = st.number_input("ROWS", min_value=3, max_value=7, value=4, key="cfg_rows")
        cols = st.number_input("COLS", min_value=3, max_value=7, value=4, key="cfg_cols")
        pits = st.number_input("PITS", min_value=1, max_value=8, value=3, key="cfg_pits")

        if st.button("🔄 GENERATE WORLD", use_container_width=True, type="primary"):
            init_state()
            st.rerun()

        st.markdown("---")
        st.markdown('<div class="panel-header">🎮 CONTROLS</div>', unsafe_allow_html=True)
        if st.button("🤖 AUTO STEP", use_container_width=True):
            auto_step()
            st.rerun()
        if st.button("👁 REVEAL ALL", use_container_width=True):
            if "initialized" in st.session_state:
                st.session_state.revealed = True
                st.rerun()

        st.markdown("---")
        st.markdown('<div class="panel-header">🗺 LEGEND</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.7rem;line-height:2.2;color:#7a9ab8">
        🤖 &nbsp;<span style="color:#00c8ff">AGENT</span><br>
        ✓ &nbsp;<span style="color:#00ff88">SAFE / VISITED</span><br>
        ⚠ &nbsp;<span style="color:#ff3355">DANGER DEDUCED</span><br>
        ? &nbsp;<span style="color:#3a5a7a">UNKNOWN</span><br>
        🕳 &nbsp;<span style="color:#ff3355">PIT (revealed)</span><br>
        👾 &nbsp;<span style="color:#ff6400">WUMPUS (revealed)</span><br>
        💰 &nbsp;<span style="color:#ffd700">GOLD</span>
        </div>
        """, unsafe_allow_html=True)

    # Auto-init
    if "initialized" not in st.session_state:
        init_state()

    s = st.session_state

    # ── Main layout: grid | sidebar ──
    col_grid, col_side = st.columns([2, 1])

    with col_grid:
        st.markdown('<div class="panel-header">🗺 WUMPUS WORLD GRID</div>', unsafe_allow_html=True)
        render_grid()

        # Status bar
        status_msg, status_type = s.status
        st.markdown(f'<div class="status-{status_type}">{status_msg}</div>', unsafe_allow_html=True)
        st.markdown("")

        # Movement buttons (directional pad)
        if not s.game_over:
            st.markdown('<div class="panel-header">🕹 MOVE AGENT</div>', unsafe_allow_html=True)
            ar, ac = s.agent_r, s.agent_c
            rows_n, cols_n = s.rows, s.cols
            adj = get_adj(ar, ac, rows_n, cols_n)

            # Build directional grid: UP, LEFT, DOWN, RIGHT
            b_col1, b_col2, b_col3, b_col4, b_col5 = st.columns([1, 1, 1, 1, 1])

            # UP = (ar-1, ac) — "higher row index = visually up"
            up    = (ar - 1, ac) if (ar - 1, ac) in adj else None
            down  = (ar + 1, ac) if (ar + 1, ac) in adj else None
            left  = (ar, ac - 1) if (ar, ac - 1) in adj else None
            right = (ar, ac + 1) if (ar, ac + 1) in adj else None

            def btn_label(cell_pos):
                if cell_pos is None:
                    return "·"
                ck = key(*cell_pos)
                if ck in s.safe_cells and ck not in s.visited:
                    return f"[{rows_n - cell_pos[0]},{cell_pos[1]+1}] ✓"
                elif ck in s.danger_cells:
                    return f"[{rows_n - cell_pos[0]},{cell_pos[1]+1}] ⚠"
                elif ck in s.visited:
                    return f"[{rows_n - cell_pos[0]},{cell_pos[1]+1}] ↩"
                return f"[{rows_n - cell_pos[0]},{cell_pos[1]+1}] ?"

            with b_col2:
                if up:
                    if st.button(f"▲ {btn_label(up)}", key="move_up", use_container_width=True):
                        move_agent(*up); st.rerun()
            with b_col1:
                if left:
                    if st.button(f"◀ {btn_label(left)}", key="move_left", use_container_width=True):
                        move_agent(*left); st.rerun()
            with b_col3:
                if down:
                    if st.button(f"▼ {btn_label(down)}", key="move_down", use_container_width=True):
                        move_agent(*down); st.rerun()
            with b_col4:
                if right:
                    if st.button(f"▶ {btn_label(right)}", key="move_right", use_container_width=True):
                        move_agent(*right); st.rerun()

    with col_side:
        # Metrics
        st.markdown('<div class="panel-header">📊 REAL-TIME METRICS</div>', unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-label">INFERENCE STEPS</div>
              <div class="metric-value">{s.inf_steps}</div>
            </div>
            <div class="metric-card">
              <div class="metric-label">SAFE DEDUCED</div>
              <div class="metric-value" style="color:#00ff88">{len([k for k in s.safe_cells if k not in s.visited])}</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-label">CELLS VISITED</div>
              <div class="metric-value">{len(s.visited)}</div>
            </div>
            <div class="metric-card">
              <div class="metric-label">DANGER DEDUCED</div>
              <div class="metric-value" style="color:#ff3355">{len(s.danger_cells)}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">KB CLAUSES</div>
          <div class="metric-value">{len(s.kb.clauses)}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        # Percepts
        st.markdown('<div class="panel-header">👁 CURRENT PERCEPTS</div>', unsafe_allow_html=True)
        if s.current_percepts:
            for p in s.current_percepts:
                st.markdown(f'<div class="percept-tag">{p}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<span style="color:#3a5a7a;font-size:0.75rem">No percepts at current cell.</span>', unsafe_allow_html=True)

        st.markdown("")
        # KB Log
        st.markdown('<div class="panel-header">📋 KNOWLEDGE BASE LOG</div>', unsafe_allow_html=True)
        log_html = '<div class="log-box">'
        for msg, cls in s.kb_log[-60:]:
            log_html += f'<div class="{cls}">{msg}</div>'
        log_html += '</div>'
        st.markdown(log_html, unsafe_allow_html=True)

        st.markdown("")
        # Inference Log
        st.markdown('<div class="panel-header">🔍 INFERENCE ENGINE LOG</div>', unsafe_allow_html=True)
        inf_html = '<div class="log-box">'
        for msg, cls in s.inf_log[-60:]:
            inf_html += f'<div class="{cls}">{msg}</div>'
        inf_html += '</div>'
        st.markdown(inf_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()