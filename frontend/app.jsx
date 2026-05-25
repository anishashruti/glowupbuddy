// Glow-Up Buddy — single-component mobile dashboard
// All hardcoded demo data. Colors come from the fig palette.

const COLORS = {
  pistachio: '#dfe0cc',
  laurel: '#aeb080',
  berry: '#d292a8',
  plum: '#631b40',
  cream: '#f6f2e9',
  white: '#ffffff',
  faded: '#e8e8e8',
  stressed: '#e08080',
  focused: '#a0b8d8',
  tired: '#c9a0c9',
};

const H = { fontFamily: '"Playfair Display", Georgia, serif', color: COLORS.plum };
const B = { fontFamily: '"Lato", system-ui, sans-serif', color: COLORS.plum };

// ─── Demo data ──────────────────────────────────────────────────
const PRIORITIES = [
  { n: 1, title: 'Drink 2L water', sub: '8oz every 90 min' },
  { n: 2, title: '30-min movement', sub: 'Pilates + walk after lunch' },
  { n: 3, title: 'Journal 5 min', sub: 'Before bed, no phone' },
];

const SCHEDULE = [
  { time: '7:00',  emoji: '🌅', task: 'Sunrise stretch + hydrate' },
  { time: '7:30',  emoji: '🍵', task: 'Matcha + skincare ritual' },
  { time: '8:15',  emoji: '📓', task: 'Morning pages, 3 things' },
  { time: '9:30',  emoji: '💻', task: 'Deep work — capstone deck' },
  { time: '12:00', emoji: '🥗', task: 'Lunch w/ Mira at Figgy' },
  { time: '1:30',  emoji: '🚶‍♀️', task: 'Walk + pod (Huberman ep.)' },
  { time: '3:00',  emoji: '🧘', task: 'Pilates @ home, 30 min' },
  { time: '5:00',  emoji: '📚', task: 'Read — Atomic Habits, ch. 4' },
  { time: '7:00',  emoji: '🍝', task: 'Slow dinner, no scrolling' },
  { time: '9:30',  emoji: '🌙', task: 'Tea, journal, lights out' },
];

const BINGO = [
  { t: 'Walk 10k steps', done: true },
  { t: 'No phone after 10pm', done: true },
  { t: 'Try a new recipe', done: false },
  { t: 'Read 50 pages', done: true },
  { t: '8h of sleep', done: false },

  { t: 'Cold shower', done: false },
  { t: 'Call grandma', done: true },
  { t: 'Meditate 15 min', done: false },
  { t: 'Save $20', done: false },
  { t: 'Stretch 10 min', done: true },

  { t: 'No takeout', done: false },
  { t: 'Hot girl walk', done: true },
  { t: 'FREE', done: false, free: true },
  { t: 'Write a letter', done: false },
  { t: 'Bed by 11', done: false },

  { t: 'No sugar day', done: false },
  { t: 'Skincare full set', done: true },
  { t: 'Inbox to zero', done: false },
  { t: 'Drink 2L water', done: true },
  { t: 'Journal 3 pages', done: false },

  { t: 'New playlist', done: false },
  { t: 'Compliment a stranger', done: false },
  { t: 'Try yoga class', done: false },
  { t: 'Tech-free morning', done: false },
  { t: 'Plan next week', done: false },
];

const REFLECTIONS = [
  {
    mood: 'happy', date: 'Wed · May 21',
    text: 'Best day in weeks. Walked along the cliffs at sunset and finally felt like myself again. The little things really do stack.',
    tasks: ['Hot girl walk', 'Read 50 pages'],
    ideas: ['Make this a weekly thing', 'Invite Mira next time'],
  },
  {
    mood: 'stressed', date: 'Tue · May 20',
    text: 'Capstone presentation in 3 days and I haven\'t opened the slides. Stomach in knots. Going to break it into 30-min blocks tomorrow.',
    tasks: ['Outline 3 sections', 'Email professor'],
    ideas: ['Pomodoro w/ Lena', 'Print cue cards'],
  },
  {
    mood: 'focused', date: 'Mon · May 19',
    text: 'Quiet, productive Monday. Coffee, no socials till noon, finished the case study draft. Lock-in mode is unmatched.',
    tasks: ['Case study draft', 'Reply to 5 emails'],
    ideas: ['Block socials till noon every day', 'Try Forest app'],
  },
  {
    mood: 'tired', date: 'Sun · May 18',
    text: 'Slept 10 hours and still drained. Did the bare minimum — skincare, two glasses of water, a slow walk. That counts.',
    tasks: ['Skincare', 'Slow walk'],
    ideas: ['Magnesium before bed', 'Lights out by 10:30'],
  },
];

const MOOD_BAR = {
  happy:    { color: COLORS.laurel,   label: 'HAPPY' },
  stressed: { color: COLORS.stressed, label: 'STRESSED' },
  focused:  { color: COLORS.focused,  label: 'FOCUSED' },
  tired:    { color: COLORS.tired,    label: 'TIRED' },
};

// ─── Reusable bits ──────────────────────────────────────────────
function ScreenHeader({ kicker, title }) {
  return (
    <div style={{ padding: '20px 22px 8px' }}>
      <div style={{
        ...B, fontSize: 11, letterSpacing: 2.4, textTransform: 'uppercase',
        fontWeight: 700, color: COLORS.berry, marginBottom: 6,
      }}>{kicker}</div>
      <h1 style={{
        ...H, fontSize: 30, fontWeight: 700, lineHeight: 1.05, margin: 0,
        letterSpacing: -0.3,
      }}>{title}</h1>
    </div>
  );
}

function Pill({ children, variant = 'berry', style = {} }) {
  const base = {
    ...B, display: 'inline-block', fontSize: 12, fontWeight: 700,
    padding: '5px 11px', borderRadius: 999, lineHeight: 1.2,
    whiteSpace: 'nowrap',
  };
  const v = variant === 'berry'
    ? { background: COLORS.berry, color: COLORS.plum }
    : { background: COLORS.white, color: COLORS.plum, border: `1.5px solid ${COLORS.laurel}` };
  return <span style={{ ...base, ...v, ...style }}>{children}</span>;
}

// ─── Screen 1 — Today's Plan ────────────────────────────────────
function TodayScreen() {
  const [schedule, setSchedule] = React.useState(SCHEDULE);
  const dragIdx = React.useRef(null);
  const [overIdx, setOverIdx] = React.useState(null);

  function handleDragStart(i) {
    dragIdx.current = i;
  }
  function handleDragOver(e, i) {
    e.preventDefault();
    if (dragIdx.current !== i) setOverIdx(i);
  }
  function handleDrop(e, i) {
    e.preventDefault();
    const from = dragIdx.current;
    if (from === null || from === i) { dragIdx.current = null; setOverIdx(null); return; }
    const next = [...schedule];
    const [moved] = next.splice(from, 1);
    next.splice(i, 0, moved);
    setSchedule(next);
    dragIdx.current = null;
    setOverIdx(null);
  }
  function handleDragEnd() {
    dragIdx.current = null;
    setOverIdx(null);
  }

  return (
    <div>
      <ScreenHeader kicker="Friday · May 23" title={<>Hey bestie!<br/>Here's your day <span style={{ color: COLORS.berry }}>✨</span></>} />

      <SectionHeading>Top 3 priorities</SectionHeading>
      <div style={{ padding: '0 22px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {PRIORITIES.map(p => (
          <div key={p.n} style={{
            background: COLORS.white, border: `1.5px solid ${COLORS.laurel}`,
            borderRadius: 14, padding: '14px 16px',
            display: 'flex', alignItems: 'center', gap: 14,
            boxShadow: '0 2px 0 rgba(99,27,64,.04)',
          }}>
            <div style={{
              width: 32, height: 32, borderRadius: 999,
              background: COLORS.berry, color: COLORS.plum,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              ...H, fontWeight: 700, fontSize: 16, flexShrink: 0,
            }}>{p.n}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ ...B, fontWeight: 700, fontSize: 15 }}>{p.title}</div>
              <div style={{ ...B, fontSize: 12, opacity: .65, marginTop: 1 }}>{p.sub}</div>
            </div>
          </div>
        ))}
      </div>

      <SectionHeading style={{ marginTop: 24 }}>Today's blocks</SectionHeading>
      <div style={{ padding: '0 22px 8px' }}>
        <div style={{ borderRadius: 14, overflow: 'hidden', border: `1.5px solid ${COLORS.laurel}` }}>
          {schedule.map((s, i) => {
            const isDragging = dragIdx.current === i;
            const isOver = overIdx === i;
            return (
              <div
                key={s.time + s.task}
                draggable
                onDragStart={() => handleDragStart(i)}
                onDragOver={(e) => handleDragOver(e, i)}
                onDrop={(e) => handleDrop(e, i)}
                onDragEnd={handleDragEnd}
                style={{
                  background: isOver ? COLORS.berry + '33' : (i % 2 === 0 ? COLORS.pistachio : COLORS.white),
                  padding: '13px 16px',
                  display: 'flex', alignItems: 'center', gap: 14,
                  borderTop: i === 0 ? 'none' : `1px solid ${COLORS.laurel}33`,
                  opacity: isDragging ? 0.35 : 1,
                  cursor: 'grab',
                  transition: 'background 0.15s ease, opacity 0.15s ease',
                  boxShadow: isOver ? `inset 0 2px 0 ${COLORS.berry}` : 'none',
                }}
              >
                <div style={{
                  display: 'flex', flexDirection: 'column', gap: 3, flexShrink: 0,
                  opacity: 0.35, paddingRight: 2,
                }}>
                  <div style={{ width: 14, display: 'flex', flexDirection: 'column', gap: 3 }}>
                    {[0,1,2].map(r => (
                      <div key={r} style={{ display: 'flex', gap: 3 }}>
                        <div style={{ width: 3, height: 3, borderRadius: 999, background: COLORS.plum }} />
                        <div style={{ width: 3, height: 3, borderRadius: 999, background: COLORS.plum }} />
                      </div>
                    ))}
                  </div>
                </div>
                <div style={{
                  ...H, fontSize: 14, fontWeight: 700, fontVariantNumeric: 'tabular-nums',
                  width: 44, flexShrink: 0,
                }}>{s.time}</div>
                <div style={{ fontSize: 20, lineHeight: 1, flexShrink: 0 }}>{s.emoji}</div>
                <div style={{ ...B, fontSize: 14, flex: 1, fontWeight: 500 }}>{s.task}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function SectionHeading({ children, style = {} }) {
  return (
    <div style={{ padding: '18px 22px 10px', ...style }}>
      <span style={{
        ...H, fontSize: 13, fontWeight: 700, color: COLORS.plum,
        textTransform: 'uppercase', letterSpacing: 2,
        background: COLORS.berry, padding: '5px 12px', borderRadius: 999,
        fontStyle: 'italic',
      }}>{children}</span>
    </div>
  );
}

// ─── Screen 2 — Bingo Board ─────────────────────────────────────
function BingoScreen() {
  const [hovered, setHovered] = React.useState(null);
  const done = BINGO.filter(b => b.done).length;
  return (
    <div>
      <ScreenHeader kicker="May challenge" title={<>Monthly <em style={{ fontStyle: 'italic' }}>bingo</em> board</>} />
      <div style={{ padding: '8px 22px 4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ ...B, fontSize: 13, opacity: .75 }}>Tap to mark a square</div>
        <Pill>{done} / 24 done</Pill>
      </div>

      <div style={{
        padding: '14px 14px 4px',
        display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 6,
      }}>
        {BINGO.map((sq, i) => {
          const isFree = sq.free;
          const isDone = sq.done;
          const isHover = hovered === i;
          return (
            <div key={i}
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
              onTouchStart={() => setHovered(i)}
              onTouchEnd={() => setHovered(null)}
              style={{
                aspectRatio: '1 / 1',
                background: isFree ? COLORS.berry : (isDone ? COLORS.faded : COLORS.white),
                border: `1.5px solid ${isHover ? COLORS.berry : COLORS.laurel}`,
                borderRadius: 12,
                padding: '6px 5px',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                textAlign: 'center',
                opacity: isDone ? 0.55 : 1,
                transform: isHover ? 'scale(1.07)' : 'scale(1)',
                boxShadow: isHover
                  ? `0 6px 18px -6px ${COLORS.berry}, 0 2px 0 rgba(99,27,64,.06)`
                  : '0 1px 0 rgba(99,27,64,.04)',
                transition: 'transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease',
                cursor: 'pointer',
                position: 'relative', zIndex: isHover ? 2 : 1,
              }}>
              {isFree ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                  <div style={{ fontSize: 22, lineHeight: 1 }}>⭐</div>
                  <div style={{ ...H, fontSize: 9, fontWeight: 700, letterSpacing: 1.5, fontStyle: 'italic' }}>FREE</div>
                </div>
              ) : (
                <div style={{
                  ...B, fontSize: 10.5, fontWeight: 600, lineHeight: 1.15,
                  textDecoration: isDone ? 'line-through' : 'none',
                }}>{sq.t}</div>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ padding: '14px 22px 8px' }}>
        <div style={{
          background: COLORS.white, border: `1.5px solid ${COLORS.laurel}`,
          borderRadius: 14, padding: '14px 16px', display: 'flex', alignItems: 'center', gap: 14,
        }}>
          <div style={{ fontSize: 26 }}>🎯</div>
          <div style={{ flex: 1 }}>
            <div style={{ ...H, fontSize: 16, fontWeight: 700 }}>You're on a 5-day streak</div>
            <div style={{ ...B, fontSize: 12, opacity: .7, marginTop: 2 }}>17 squares left — pick a quick one tonight?</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Screen 3 — Reflections ─────────────────────────────────────
function VibesScreen() {
  return (
    <div>
      <ScreenHeader kicker="Vibes journal" title={<>Recent <em style={{ fontStyle: 'italic' }}>reflections</em></>} />
      <div style={{ padding: '12px 22px 8px', display: 'flex', flexDirection: 'column', gap: 14 }}>
        {REFLECTIONS.map((r, i) => (
          <div key={i} style={{
            background: COLORS.white, borderRadius: 14, overflow: 'hidden',
            borderLeft: `6px solid ${MOOD_BAR[r.mood].color}`,
            border: `1.5px solid ${COLORS.laurel}`,
            borderLeftWidth: 6, borderLeftColor: MOOD_BAR[r.mood].color,
            padding: '14px 16px',
            boxShadow: '0 2px 0 rgba(99,27,64,.04)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 6 }}>
              <div style={{
                ...B, fontSize: 10, fontWeight: 800, letterSpacing: 1.8,
                color: MOOD_BAR[r.mood].color, textTransform: 'uppercase',
              }}>{MOOD_BAR[r.mood].label}</div>
              <div style={{ ...B, fontSize: 11, opacity: .6, whiteSpace: 'nowrap' }}>{r.date}</div>
            </div>
            <div style={{ ...B, fontSize: 14, lineHeight: 1.5, marginBottom: 10 }}>{r.text}</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {r.tasks.map((t, j) => <Pill key={`t${j}`} variant="berry">{t}</Pill>)}
              {r.ideas.map((t, j) => <Pill key={`i${j}`} variant="outline">💡 {t}</Pill>)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Screen 4 — Profile ────────────────────────────────────────
const PATTERNS_DEFAULT = [
  'You like to work in the morning',
  'You love Pilates on Mondays & Wednesdays',
  'You do grocery shopping on weekends',
  'You plan your meals on Saturdays',
];

function ProfileScreen() {
  const [patterns, setPatterns] = React.useState(PATTERNS_DEFAULT);
  const [editIdx, setEditIdx]   = React.useState(null);
  const [editVal, setEditVal]   = React.useState('');
  const dragIdx = React.useRef(null);
  const [overIdx, setOverIdx]   = React.useState(null);

  function startEdit(i) { setEditIdx(i); setEditVal(patterns[i]); }
  function commitEdit(i) {
    if (editVal.trim()) {
      const next = [...patterns];
      next[i] = editVal.trim();
      setPatterns(next);
    }
    setEditIdx(null);
  }
  function handleDragStart(i) { dragIdx.current = i; }
  function handleDragOver(e, i) { e.preventDefault(); if (dragIdx.current !== i) setOverIdx(i); }
  function handleDrop(e, i) {
    e.preventDefault();
    const from = dragIdx.current;
    if (from === null || from === i) { dragIdx.current = null; setOverIdx(null); return; }
    const next = [...patterns];
    const [moved] = next.splice(from, 1);
    next.splice(i, 0, moved);
    setPatterns(next);
    dragIdx.current = null;
    setOverIdx(null);
  }
  function handleDragEnd() { dragIdx.current = null; setOverIdx(null); }

  return (
    <div>
      <div style={{ padding: '20px 22px 8px' }}>
        <div style={{ ...B, fontSize: 11, letterSpacing: 2.4, textTransform: 'uppercase', fontWeight: 700, color: COLORS.berry, marginBottom: 6 }}>your profile</div>
        <h1 style={{ ...H, fontSize: 30, fontWeight: 700, lineHeight: 1.05, margin: 0, letterSpacing: -0.3 }}>
          Hey Anisha <span style={{ color: COLORS.berry }}>✨</span>
        </h1>
        <p style={{ ...B, fontSize: 13, opacity: .65, margin: '6px 0 0' }}>Here's what I know about you so far.</p>
      </div>

      <SectionHeading style={{ marginTop: 16 }}>Your patterns</SectionHeading>
      <div style={{ padding: '0 22px 8px' }}>
        <div style={{ ...B, fontSize: 12, opacity: .6, marginBottom: 10 }}>Tap to edit · drag to reorder</div>
        <div style={{ borderRadius: 14, overflow: 'hidden', border: `1.5px solid ${COLORS.laurel}` }}>
          {patterns.map((p, i) => {
            const isDragging = dragIdx.current === i;
            const isOver     = overIdx === i;
            const isEditing  = editIdx === i;
            return (
              <div
                key={i}
                draggable={!isEditing}
                onDragStart={() => handleDragStart(i)}
                onDragOver={(e) => handleDragOver(e, i)}
                onDrop={(e) => handleDrop(e, i)}
                onDragEnd={handleDragEnd}
                style={{
                  background: isOver ? COLORS.berry + '33' : (i % 2 === 0 ? COLORS.pistachio : COLORS.white),
                  padding: '13px 14px',
                  display: 'flex', alignItems: 'center', gap: 10,
                  borderTop: i === 0 ? 'none' : `1px solid ${COLORS.laurel}33`,
                  opacity: isDragging ? 0.35 : 1,
                  cursor: isEditing ? 'default' : 'grab',
                  transition: 'background 0.15s ease, opacity 0.15s ease',
                  boxShadow: isOver ? `inset 0 2px 0 ${COLORS.berry}` : 'none',
                }}
              >
                {!isEditing && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 3, flexShrink: 0, opacity: 0.3 }}>
                    {[0,1,2].map(r => (
                      <div key={r} style={{ display: 'flex', gap: 3 }}>
                        <div style={{ width: 3, height: 3, borderRadius: 999, background: COLORS.plum }} />
                        <div style={{ width: 3, height: 3, borderRadius: 999, background: COLORS.plum }} />
                      </div>
                    ))}
                  </div>
                )}
                <div style={{ fontSize: 15, flexShrink: 0 }}>✨</div>
                {isEditing ? (
                  <input
                    autoFocus
                    value={editVal}
                    onChange={e => setEditVal(e.target.value)}
                    onBlur={() => commitEdit(i)}
                    onKeyDown={e => { if (e.key === 'Enter') commitEdit(i); if (e.key === 'Escape') setEditIdx(null); }}
                    style={{
                      flex: 1, border: 'none', outline: 'none', background: 'transparent',
                      ...B, fontSize: 14, fontWeight: 500, color: COLORS.plum,
                    }}
                  />
                ) : (
                  <div
                    onClick={() => startEdit(i)}
                    style={{ ...B, fontSize: 14, flex: 1, fontWeight: 500, cursor: 'text', lineHeight: 1.4 }}
                  >{p}</div>
                )}
                {!isEditing && (
                  <button
                    onClick={() => startEdit(i)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4, opacity: 0.35, flexShrink: 0 }}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={COLORS.plum} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ─── Bottom nav ────────────────────────────────────────────────
const TABS = [
  { id: 'today', label: 'Today', emoji: '📅' },
  { id: 'bingo', label: 'Bingo', emoji: '🎯' },
  { id: 'vibes', label: 'Vibes', emoji: '💬' },
];

function BottomNav({ active, onChange }) {
  return (
    <div style={{
      position: 'sticky', bottom: 0, left: 0, right: 0,
      background: COLORS.white,
      borderTop: `1.5px solid ${COLORS.laurel}`,
      padding: '10px 16px 14px',
      display: 'flex', justifyContent: 'space-around',
      zIndex: 10,
    }}>
      {TABS.map(t => {
        const isActive = active === t.id;
        return (
          <button key={t.id} onClick={() => onChange(t.id)} style={{
            border: 'none', background: 'transparent', cursor: 'pointer',
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
            padding: 0, minWidth: 72,
          }}>
            <div style={{
              padding: '6px 18px', borderRadius: 999,
              background: isActive ? COLORS.berry : 'transparent',
              transition: 'background .18s ease',
              fontSize: 20, lineHeight: 1,
            }}>{t.emoji}</div>
            <div style={{
              ...B, fontSize: 11, fontWeight: isActive ? 800 : 500,
              color: isActive ? COLORS.plum : '#9b8d92',
              letterSpacing: .3,
            }}>{t.label}</div>
          </button>
        );
      })}
    </div>
  );
}

// ─── Sparkles (decorative, around the frame) ───────────────────
function Sparkles() {
  // Positions are % within the device frame
  const SPARKS = [
    { top: '6%',  left: '6%',  size: 14, delay: 0,    dur: 3.2 },
    { top: '10%', right: '10%', size: 10, delay: .7,  dur: 2.8 },
    { top: '38%', left: '-3%', size: 12, delay: 1.4, dur: 3.6 },
    { top: '52%', right: '-2%', size: 16, delay: .3,  dur: 3.0 },
    { top: '74%', left: '4%',  size: 9,  delay: 1.9, dur: 2.6 },
    { top: '86%', right: '8%', size: 13, delay: .9,  dur: 3.4 },
    { top: '22%', right: '-4%', size: 9,  delay: 2.2, dur: 3.1 },
    { top: '64%', left: '-4%', size: 10, delay: 1.1, dur: 2.9 },
  ];
  const star = (
    <svg viewBox="0 0 100 100" width="100%" height="100%">
      <path fill="currentColor" d="M50 0 C58 36 64 42 100 50 C64 58 58 64 50 100 C42 64 36 58 0 50 C36 42 42 36 50 0Z"/>
    </svg>
  );
  return (
    <div style={{
      position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 100,
      overflow: 'visible',
    }}>
      {SPARKS.map((s, i) => (
        <div key={i} style={{
          position: 'absolute',
          top: s.top, left: s.left, right: s.right,
          width: s.size, height: s.size,
          color: i % 2 === 0 ? COLORS.berry : COLORS.laurel,
          animation: `gub-sparkle ${s.dur}s ease-in-out ${s.delay}s infinite`,
          filter: 'drop-shadow(0 1px 0 rgba(99,27,64,.15))',
        }}>{star}</div>
      ))}
    </div>
  );
}

// ─── App shell ─────────────────────────────────────────────────
function App() {
  const [screen, setScreen] = React.useState('today');
  const [prevScreen, setPrevScreen] = React.useState('today');
  const onProfile = screen === 'profile';

  function openProfile() { setPrevScreen(screen); setScreen('profile'); }
  function closeProfile() { setScreen(prevScreen); }

  return (
    <div style={{
      width: '100%', height: '100%',
      background: COLORS.pistachio,
      display: 'flex', flexDirection: 'column',
      position: 'relative', overflow: 'hidden',
    }}>
      {/* Top bar */}
      <div style={{
        flexShrink: 0,
        padding: '52px 18px 4px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        {onProfile ? (
          <button
            onClick={closeProfile}
            style={{
              background: 'none', border: 'none', cursor: 'pointer', padding: 0,
              display: 'flex', alignItems: 'center', gap: 6,
              ...B, fontWeight: 700, fontSize: 14, color: COLORS.plum,
            }}
          >
            <svg width="9" height="16" viewBox="0 0 9 16" fill="none">
              <path d="M8 1L1 8l7 7" stroke={COLORS.plum} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Back
          </button>
        ) : (
          <img src="assets/logo.png" alt="Glow-Up Buddy"
               style={{ height: 56, width: 'auto', display: 'block' }} />
        )}
        <div
          onClick={onProfile ? closeProfile : openProfile}
          style={{
            width: 38, height: 38, borderRadius: 999,
            background: onProfile ? COLORS.plum : COLORS.berry,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            ...H, fontWeight: 700, fontSize: 15,
            color: onProfile ? COLORS.cream : COLORS.plum,
            border: `1.5px solid ${COLORS.plum}22`,
            cursor: 'pointer',
            transition: 'background 0.2s ease, color 0.2s ease',
          }}
        >A</div>
      </div>

      {/* Scrollable content */}
      <div style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', position: 'relative' }}>
        {screen === 'today'   && <TodayScreen />}
        {screen === 'bingo'   && <BingoScreen />}
        {screen === 'vibes'   && <VibesScreen />}
        {screen === 'profile' && <ProfileScreen />}
        <div style={{ height: 16 }} />
      </div>

      {!onProfile && <BottomNav active={screen} onChange={setScreen} />}
      <Sparkles />
    </div>
  );
}

window.App = App;
