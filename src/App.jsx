import React, { useState, useEffect, useRef } from 'react';
import './App.css';

/* ==========================================================================
   CONFIG & PERSONALIZATION
   Natural, simple, heartfelt words from lunchbox to his favorite girl ♡
   ========================================================================== */
const CONFIG = {
  MY_NAME: "lunchbox",
  HER_NAME: "Baby",
  HER_NICKNAME: "My Favorite Human",
  ANNIVERSARY_LABEL: "365 Days Together",
  ANNIVERSARY_DATE: "One Year Completed",

  // ACT I — The Threshold
  ACT_1: {
    badge: "✦ OUR LITTLE UNIVERSE ✦",
    whisper: "Put on your headphones, take your time okay? I made this for you 🎧💗",
    headline: "One whole year.\nSo many feelings for you.",
    subtext: "You know my English is not super perfect hehe, but every single word here is 100% from my heart for you.",
    button: "Open our little world ♡",
    signature: "made with all my love, by lunchbox"
  },

  // ACT II — The Unhurried Love Letter (3 Pages)
  ACT_2: {
    salutation: "To my favorite person in the world,",
    pages: [
      {
        pageNumber: 1,
        title: "How 1 Year Passed So Fast",
        paragraphs: [
          "Can you believe it? One whole year completed with you! 🥹",
          "Sometimes I think about the first day we started talking. I was so nervous honestly! I was thinking what should I text, will she reply, will she like talking to me? Hehe.",
          "And now look at us. 365 days gone just like that. But every single day with you felt so nice and so special to me.",
          "Time passed so fast, but I remember all the small moments we shared. I really feel so lucky that I have you in my life."
        ],
        marginNote: "remember our first chats? I was checking my phone every 2 minutes 🙈"
      },
      {
        pageNumber: 2,
        title: "Why You Mean So Much To Me",
        paragraphs: [
          "You know I am not good with big fancy words, but I just want to tell you how much you mean to me.",
          "I love how you talk to me, how you laugh at my silly jokes, and how you care for me even in small small things. When I have a bad day or feel tired, just talking to you for 5 minutes makes everything okay.",
          "With you, I don't have to pretend to be someone else. I can just be myself, be silly, and you still love me. That is the best feeling in the whole world."
        ],
        marginNote: "you're still my favorite notification, every single day 📱✨"
      },
      {
        pageNumber: 3,
        title: "Our Simple Everyday Days",
        paragraphs: [
          "My favorite thing is not fancy dates or anything big. It's just our normal, everyday moments.",
          "Asking each other 'did you eat?', our silly inside jokes that nobody else understands, talking late at night, and saying goodnight before sleeping.",
          "Thank you for being with me this one whole year, babyyy. Thank you for your patience with me and for loving me so much.",
          "Happy 1 year anniversary to us! I love you so much, more than my words can explain. 💗"
        ],
        marginNote: "lunchbox loves you always and forever, no matter what 🧸🫶🏻"
      }
    ],
    closing: "always yours,",
    nextButton: "See our 12 months journey →"
  },

  // ACT III — The 12-Month Constellation of Us
  ACT_3: {
    heading: "12 Little Chapters. Our Story.",
    subtext: "A whole year of us, month by month. Tap any star to see that month's sweet memory! ✨",
    chapters: [
      {
        month: 1,
        title: "The First Month",
        tagline: "Month 01",
        reflection: "When we started talking. I was smiling like an idiot looking at my phone every time your name popped up on my screen.",
        learned: "How fast you can make my heart beat just with one message.",
        melody: "♫ That first spark — when I realized you are so special."
      },
      {
        month: 2,
        title: "Talking Every Day",
        tagline: "Month 02",
        reflection: "We started talking daily without missing a single day. The shyness went away and you slowly became my favorite habit.",
        learned: "Your laugh is honestly my most favorite sound in the world.",
        melody: "♫ Golden feelings — when everything felt warm with you."
      },
      {
        month: 3,
        title: "Our Silly Jokes",
        tagline: "Month 03",
        reflection: "We got so comfortable with each other. Making silly jokes, teasing each other, and laughing together till late at night.",
        learned: "When you get playfully stubborn, you look the cutest.",
        melody: "♫ Finding comfort — like I found my home in you."
      },
      {
        month: 4,
        title: "My Comfort Person",
        tagline: "Month 04",
        reflection: "Whenever I had stress or tension, your voice was like medicine for me. You just calmed me down so easily.",
        learned: "You care so deeply about me, even in small little things.",
        melody: "♫ Yellow — Look at the stars, look how they shine for you."
      },
      {
        month: 5,
        title: "Knowing You More",
        tagline: "Month 05",
        reflection: "Learning small things about you—what you like, what makes you angry, what makes you smile. I liked everything about you.",
        learned: "You have such a kind and soft heart inside.",
        melody: "♫ Lover — Can we always be this close forever?"
      },
      {
        month: 6,
        title: "Half Year Done!",
        tagline: "Month 06",
        reflection: "6 months completed with you! It felt like just a few weeks. I remember thinking 'I never want this feeling to end'.",
        learned: "Time really flies so fast when I am talking to you.",
        melody: "♫ A Thousand Years — I loved you for 6 months, and I will love you for 1000 more."
      },
      {
        month: 7,
        title: "Always There For Me",
        tagline: "Month 07",
        reflection: "Even on busy days, just knowing I have you to talk to in the evening made my whole day feel good and peaceful.",
        learned: "Just a 2-minute call with you can fix my bad mood completely.",
        melody: "♫ Here With Me — Just being around you is enough for me."
      },
      {
        month: 8,
        title: "So Many Sweet Smiles",
        tagline: "Month 08",
        reflection: "So many small sweet memories. Nothing fancy, just you and me laughing together and being happy.",
        learned: "You make normal ordinary days feel so special.",
        melody: "♫ Beyond — Sometimes you feel too good to be true, but you're mine."
      },
      {
        month: 9,
        title: "Understanding Each Other",
        tagline: "Month 09",
        reflection: "Now we understand each other without even saying much. Just by reading your text I know your mood.",
        learned: "Having you in my life is honestly my biggest luck.",
        melody: "♫ Stand By Me — No matter what happens, we stand together."
      },
      {
        month: 10,
        title: "Growing Closer",
        tagline: "Month 10",
        reflection: "10 months together. Every single month I just appreciate you more and more. Our bond became so strong.",
        learned: "I can trust you with everything in my life.",
        melody: "♫ Simply The Best — You are truly the best girl for me."
      },
      {
        month: 11,
        title: "Almost One Year!",
        tagline: "Month 11",
        reflection: "We realized our 1-year anniversary was coming so close. My heart still feels the exact same butterflies as day 1.",
        learned: "My love for you doesn't get old; it just keeps increasing.",
        melody: "♫ Make You Feel My Love — I always want to make you feel loved."
      },
      {
        month: 12,
        title: "365 Days of Us ♡",
        tagline: "Month 12",
        reflection: "One full year! We made it, babyyy. 365 days of you being my girl. Here is to our first year and to many more years together.",
        learned: "Choosing you was the easiest, best decision I ever made.",
        melody: "♫ Our Song — The sweet story of you and me."
      }
    ],
    nextButton: "Read some honest truths from my heart 🌸 →"
  },

  // ACT IV — Little Vulnerabilities & Secret Notes
  ACT_4: {
    heading: "Some Honest Things From My Heart 🌸",
    subtext: "Small, honest truths I don't always say out loud, but I feel every single day.",
    cards: [
      {
        id: 1,
        tag: "TRUTH 01",
        title: "I Fell For You So Hard",
        content: "Honestly, I didn't even realize when I fell so deeply in love with you. It just happened so naturally, and now I can't imagine my life without you.",
        whisper: "I love you so much, no doubts at all."
      },
      {
        id: 2,
        tag: "TRUTH 02",
        title: "Your Voice Is My Peace",
        content: "Whenever my day is stressful or irritating, hearing your voice makes everything quiet and peaceful inside my head. You just calm me down.",
        whisper: "You are my favorite medicine."
      },
      {
        id: 3,
        tag: "TRUTH 03",
        title: "Even On Bad Mood Days",
        content: "Sometimes we might have small misunderstandings or bad mood days, but even on those days, you are still the only person I want to talk to.",
        whisper: "I will always choose you, every single day."
      },
      {
        id: 4,
        tag: "TRUTH 04",
        title: "You Feel Like Home",
        content: "People say home is a house, but for me, wherever you are and whenever I talk to you, that is where I feel most safe and happy.",
        whisper: "You became my home this year."
      }
    ],
    scratchPrompt: "Tap this seal to see what I always pray for you 💌",
    scratchRevealed: "✦ 'I always pray to God that you stay happy, smiling, and always with me.' ✦",
    nextButton: "Enter the Midnight Sky 🌌 →"
  },

  // ACT V — The Celestial Climax
  ACT_5: {
    beat1: "AND JUST LIKE THAT... 🌌",
    beat2: "365 days of you and me together. ♡",
    hero: "HAPPY 1ST ANNIVERSARY, MY BABYYY!! 🎀💗",
    climaxProse: [
      "I know my English is not perfect and I don't know fancy words to write.",
      "But I made this little website with my own hands just to make you smile and feel special today.",
      "Thank you for being the sweetest, most caring girlfriend in the whole world.",
      "Happy 1 year to us! I love you so much, babyyy. Forever and always. 🫶🏻"
    ],
    certificateTitle: "OFFICIAL 1-YEAR LOVE CERTIFICATE",
    certificateDate: "365 Days & Counting",
    certificateSign: "lunchbox ♡",
    hugButton: "One big tight hug? 🫂",
    hugMessage: "BIGGEST TIGHTEST VIRTUAL HUGGG FOR YOUUU!! 💗🧸💋",
    hugSub: "Hold this close to your heart today, babyyy. I love you so much.",
    replay: "Experience our story again ↺"
  }
};

// Deterministic ambient sparkles
const STATIC_SPARKLES = Array.from({ length: 36 }).map((_, i) => ({
  id: i,
  left: `${(i * 17.7 + 3) % 94 + 3}%`,
  top: `${(i * 28.3 + 5) % 90 + 5}%`,
  size: 5 + (i % 3) * 3,
  delay: `${(i * 0.25) % 3.5}s`,
  duration: `${2.8 + (i % 3)}s`
}));

// Floating background stickers
const STATIC_DRIFT_ITEMS = Array.from({ length: 14 }).map((_, i) => ({
  id: i,
  left: `${(i * 14.3 + 6) % 88 + 6}%`,
  delay: `${i * 1.3}s`,
  duration: `${12 + (i % 4) * 2.5}s`,
  size: 14 + (i % 3) * 6,
  symbol: i % 4 === 0 ? '🎀' : i % 4 === 1 ? '🧸' : i % 4 === 2 ? '💗' : '✨'
}));

export default function App() {
  const [currentAct, setCurrentAct] = useState(1);
  const [activeLetterPage, setActiveLetterPage] = useState(0);
  const [activeMonthIdx, setActiveMonthIdx] = useState(null);
  const [expandedCardId, setExpandedCardId] = useState(null);
  const [secretRevealed, setSecretRevealed] = useState(false);
  const [climaxStep, setClimaxStep] = useState(1);
  const [hugGiven, setHugGiven] = useState(false);
  const [particles, setParticles] = useState([]);
  const [cursorPos, setCursorPos] = useState({ x: -100, y: -100, visible: false });

  // Floating particles generator
  const triggerBurst = (x, y, count = 20, emojiSet = ['💗', '♡', '✨', '🎀', '🧸', '🌷', '💋']) => {
    const originX = x || window.innerWidth / 2;
    const originY = y || window.innerHeight / 2;
    const newItems = Array.from({ length: count }).map((_, i) => {
      const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.4;
      const speed = 50 + Math.random() * 90;
      return {
        id: Date.now() + i + Math.random(),
        x: originX,
        y: originY,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 30,
        symbol: emojiSet[i % emojiSet.length],
        size: 16 + Math.random() * 12
      };
    });
    setParticles((prev) => [...prev.slice(-35), ...newItems]);
    setTimeout(() => {
      setParticles([]);
    }, 1100);
  };

  const goToAct = (actNum, e) => {
    if (e && e.clientX) {
      triggerBurst(e.clientX, e.clientY, 16);
    }
    if (actNum === 5) {
      setClimaxStep(1);
      setTimeout(() => setClimaxStep(2), 1200);
      setTimeout(() => setClimaxStep(3), 2600);
    }
    setCurrentAct(actNum);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Heart-shaped constellation coordinates for the 12 months
  const constellationStars = CONFIG.ACT_3.chapters.map((ch, idx) => {
    const t = (Math.PI * 2 * idx) / 12 - Math.PI / 2;
    const hx = 16 * Math.pow(Math.sin(t), 3);
    const hy = -(13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t));
    const scale = 8.5;
    const x = 180 + hx * scale;
    const y = 185 + hy * scale;
    return { ...ch, x, y };
  });

  const constellationPath = constellationStars
    .map((s, idx) => `${idx === 0 ? 'M' : 'L'} ${s.x.toFixed(1)} ${s.y.toFixed(1)}`)
    .join(' ') + ' Z';

  return (
    <div
      className={`universe-experience act-theme-${currentAct}`}
      onMouseMove={(e) => setCursorPos({ x: e.clientX + 14, y: e.clientY + 14, visible: true })}
      onMouseLeave={() => setCursorPos((p) => ({ ...p, visible: false }))}
    >
      {/* Desktop subtle floating cursor heart */}
      {cursorPos.visible && (
        <span
          className="desktop-cursor-heart"
          style={{ left: `${cursorPos.x}px`, top: `${cursorPos.y}px` }}
          aria-hidden="true"
        >
          💗
        </span>
      )}

      {/* Ambient background stars & drifting stickers */}
      <div className="ambient-celestial-canvas" aria-hidden="true">
        {STATIC_SPARKLES.map((sp) => (
          <span
            key={sp.id}
            className="ambient-sparkle-dot"
            style={{
              left: sp.left,
              top: sp.top,
              animationDelay: sp.delay,
              animationDuration: sp.duration,
              fontSize: `${sp.size}px`
            }}
          >
            ✦
          </span>
        ))}
        {STATIC_DRIFT_ITEMS.map((item) => (
          <span
            key={item.id}
            className="ambient-drifter"
            style={{
              left: item.left,
              animationDelay: item.delay,
              animationDuration: item.duration,
              fontSize: `${item.size}px`
            }}
          >
            {item.symbol}
          </span>
        ))}
      </div>

      {/* Interactive Click Particles */}
      {particles.map((p) => (
        <span
          key={p.id}
          className="click-burst-item"
          style={{
            left: `${p.x}px`,
            top: `${p.y}px`,
            '--vx': `${p.vx}px`,
            '--vy': `${p.vy}px`,
            fontSize: `${p.size}px`
          }}
        >
          {p.symbol}
        </span>
      ))}

      {/* Top Experience Navigation & Progress */}
      <header className="experience-navbar">
        <div className="navbar-tag">
          <span className="navbar-ribbon">🎀</span>
          <span className="navbar-label">our little universe ♡</span>
        </div>
        <nav className="act-stepper" aria-label="Story Acts">
          {[1, 2, 3, 4, 5].map((step) => (
            <button
              key={step}
              type="button"
              className={`act-pill-btn ${currentAct === step ? 'active' : ''}`}
              onClick={(e) => goToAct(step, e)}
              aria-label={`Go to Act ${step}`}
              title={`Act ${step}`}
            >
              <span className="act-pill-icon">
                {step === 1 ? '🎀' : step === 2 ? '💌' : step === 3 ? '✨' : step === 4 ? '🌸' : '🌌'}
              </span>
              <span className="act-pill-text">Act {step}</span>
            </button>
          ))}
        </nav>
      </header>

      {/* MAIN STORY CONTAINER */}
      <main className="story-stage">

        {/* ===================================================================
            ACT I — THE THRESHOLD
            =================================================================== */}
        {currentAct === 1 && (
          <section className="act-container act-1-threshold" aria-label="Act 1: The Threshold">
            <div className="sacred-badge">
              <span className="sacred-sparkle">✦</span>
              <span>{CONFIG.ACT_1.badge}</span>
              <span className="sacred-sparkle">✦</span>
            </div>

            <div className="headphone-whisper">
              <span>{CONFIG.ACT_1.whisper}</span>
            </div>

            {/* Glowing Interactive Heart Key */}
            <div
              className="threshold-heart-key"
              onClick={(e) => triggerBurst(e.clientX, e.clientY, 24)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter') triggerBurst(); }}
              title="Tap for a gentle pulse ♡"
            >
              <div className="heart-key-halo" />
              <div className="heart-key-body">
                <svg viewBox="0 0 100 90" className="threshold-heart-svg">
                  <path
                    d="M 50,23 C 30,-3 0,11 0,43 C 0,66 26,81 50,90 C 74,81 100,66 100,43 C 100,11 70,-3 50,23 Z"
                    fill="url(#thresholdGrad)"
                  />
                  <defs>
                    <linearGradient id="thresholdGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#FFF4F7" />
                      <stop offset="45%" stopColor="#FFADC2" />
                      <stop offset="100%" stopColor="#E26588" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="threshold-face">
                  <span className="face-eyes">^&nbsp;ˬ&nbsp;^</span>
                  <span className="face-tag">{CONFIG.HER_NICKNAME}</span>
                </div>
              </div>
            </div>

            <h1 className="threshold-headline">
              <span>One whole year.</span>
              <span className="threshold-headline-accent">So many feelings for you.</span>
            </h1>

            <p className="threshold-subtext">{CONFIG.ACT_1.subtext}</p>

            <button
              type="button"
              className="grand-romantic-btn"
              onClick={(e) => goToAct(2, e)}
            >
              <span>{CONFIG.ACT_1.button}</span>
              <span className="btn-sparkle">✨</span>
            </button>

            <div className="threshold-signature">
              <span>♡ {CONFIG.ACT_1.signature} ♡</span>
            </div>
          </section>
        )}

        {/* ===================================================================
            ACT II — THE UNHURRIED LOVE LETTER (3 Pages)
            =================================================================== */}
        {currentAct === 2 && (
          <section className="act-container act-2-letter" aria-label="Act 2: The Unhurried Love Letter">
            <div className="sacred-badge">
              <span>💌 ACT II — A LETTER FOR YOUR HEART 💌</span>
            </div>

            <h2 className="section-title">Take your time reading every word.</h2>
            <p className="section-subtext">Three pages written just for you, from the deepest corner of my heart.</p>

            {/* Page Navigation Tabs */}
            <div className="letter-page-tabs" role="tablist">
              {CONFIG.ACT_2.pages.map((p, idx) => (
                <button
                  key={p.pageNumber}
                  type="button"
                  role="tab"
                  aria-selected={activeLetterPage === idx}
                  className={`letter-tab-btn ${activeLetterPage === idx ? 'active' : ''}`}
                  onClick={(e) => {
                    triggerBurst(e.clientX, e.clientY, 8, ['💌', '♡', '✨']);
                    setActiveLetterPage(idx);
                  }}
                >
                  <span className="tab-num">Page 0{p.pageNumber}</span>
                  <span className="tab-title">{p.title}</span>
                </button>
              ))}
            </div>

            {/* Tactile Parchment Paper */}
            <div className="parchment-sheet">
              <div className="parchment-washi-tape" />

              <div className="parchment-top">
                <span className="parchment-stamp">365 DAYS TOGETHER 🌸</span>
                <span className="parchment-page-indicator">
                  Page {activeLetterPage + 1} of {CONFIG.ACT_2.pages.length}
                </span>
              </div>

              <h3 className="parchment-page-heading">
                {CONFIG.ACT_2.pages[activeLetterPage].title}
              </h3>

              <div className="parchment-body">
                {activeLetterPage === 0 && (
                  <p className="parchment-salutation">{CONFIG.ACT_2.salutation}</p>
                )}
                {CONFIG.ACT_2.pages[activeLetterPage].paragraphs.map((para, i) => (
                  <p key={i} className="parchment-para">{para}</p>
                ))}
              </div>

              {/* Handwritten Margin Whispers */}
              <div className="parchment-margin-note">
                <span className="note-pin">📎</span>
                <span className="note-text">"{CONFIG.ACT_2.pages[activeLetterPage].marginNote}"</span>
              </div>

              {/* Page Navigator Bottom Controls */}
              <div className="parchment-page-controls">
                <button
                  type="button"
                  className="page-nav-arrow"
                  disabled={activeLetterPage === 0}
                  onClick={() => setActiveLetterPage((prev) => Math.max(0, prev - 1))}
                >
                  ← Previous Page
                </button>
                <div className="page-dots-row">
                  {[0, 1, 2].map((idx) => (
                    <span
                      key={idx}
                      className={`page-dot ${activeLetterPage === idx ? 'active' : ''}`}
                    />
                  ))}
                </div>
                <button
                  type="button"
                  className="page-nav-arrow"
                  disabled={activeLetterPage === CONFIG.ACT_2.pages.length - 1}
                  onClick={() =>
                    setActiveLetterPage((prev) => Math.min(CONFIG.ACT_2.pages.length - 1, prev + 1))
                  }
                >
                  Next Page →
                </button>
              </div>

              {/* Signoff on the final page */}
              {activeLetterPage === CONFIG.ACT_2.pages.length - 1 && (
                <div className="letter-final-signoff">
                  <p className="signoff-closing">{CONFIG.ACT_2.closing}</p>
                  <p className="signoff-name">{CONFIG.MY_NAME} ♡</p>
                </div>
              )}
            </div>

            <div className="act-forward-action">
              <button
                type="button"
                className="grand-romantic-btn"
                onClick={(e) => goToAct(3, e)}
              >
                <span>{CONFIG.ACT_2.nextButton}</span>
              </button>
            </div>
          </section>
        )}

        {/* ===================================================================
            ACT III — THE 12-MONTH CONSTELLATION OF US
            =================================================================== */}
        {currentAct === 3 && (
          <section className="act-container act-3-constellation" aria-label="Act 3: The 12-Month Constellation">
            <div className="sacred-badge">
              <span>✨ ACT III — OUR 12 CHAPTERS ✨</span>
            </div>

            <h2 className="section-title">{CONFIG.ACT_3.heading}</h2>
            <p className="section-subtext">{CONFIG.ACT_3.subtext}</p>

            {/* Heart Constellation SVG Map */}
            <div className="constellation-frame">
              <svg
                viewBox="0 0 360 360"
                className="constellation-orbit-svg"
                aria-label="Heart shaped constellation of 12 months"
              >
                <defs>
                  <linearGradient id="orbitGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="rgba(247, 159, 183, 0.3)" />
                    <stop offset="50%" stopColor="rgba(232, 200, 139, 0.5)" />
                    <stop offset="100%" stopColor="rgba(247, 159, 183, 0.3)" />
                  </linearGradient>
                </defs>

                {/* Connecting perimeter boundary */}
                <path d={constellationPath} className="orbit-perimeter-path" />

                {/* Center cross lines */}
                {constellationStars.map((st, i) => (
                  <line
                    key={`line-${i}`}
                    x1="180"
                    y1="185"
                    x2={st.x}
                    y2={st.y}
                    className="orbit-spoke"
                  />
                ))}

                {/* Center you + me hub */}
                <g className="orbit-center-hub" transform="translate(180, 185)">
                  <circle r="22" className="hub-circle" />
                  <text y="4" textAnchor="middle" className="hub-text">you + me</text>
                </g>

                {/* 12 Interactive Month Stars */}
                {constellationStars.map((star, idx) => {
                  const isSelected = activeMonthIdx === idx;
                  return (
                    <g
                      key={star.month}
                      className={`star-node-group ${isSelected ? 'selected' : ''}`}
                      transform={`translate(${star.x}, ${star.y})`}
                      onClick={(e) => {
                        triggerBurst(e.clientX, e.clientY, 12, ['✨', '💗', '♡']);
                        setActiveMonthIdx(idx);
                      }}
                      role="button"
                      tabIndex={0}
                      aria-label={`Month ${star.month}: ${star.title}`}
                      onKeyDown={(e) => { if (e.key === 'Enter') setActiveMonthIdx(idx); }}
                    >
                      <circle r={isSelected ? "17" : "13"} className="star-aura" />
                      <circle r={isSelected ? "8" : "6"} className="star-nucleus" />
                      <text y="16" textAnchor="middle" className="star-num-label">
                        {String(star.month).padStart(2, '0')}
                      </text>
                    </g>
                  );
                })}
              </svg>

              {/* Mobile Quick Chips */}
              <div className="month-quick-pills">
                {CONFIG.ACT_3.chapters.map((ch, idx) => (
                  <button
                    key={ch.month}
                    type="button"
                    className={`month-pill ${activeMonthIdx === idx ? 'active' : ''}`}
                    onClick={(e) => {
                      triggerBurst(e.clientX, e.clientY, 8);
                      setActiveMonthIdx(idx);
                    }}
                  >
                    M{ch.month}
                  </button>
                ))}
              </div>
            </div>

            {/* Chapter Detail Overlay Modal */}
            {activeMonthIdx !== null && (
              <div className="chapter-modal-overlay" role="dialog" aria-modal="true">
                <div className="chapter-modal-card">
                  <div className="modal-header">
                    <span className="modal-tag">✦ {CONFIG.ACT_3.chapters[activeMonthIdx].tagline} ✦</span>
                    <button
                      type="button"
                      className="modal-close-btn"
                      onClick={() => setActiveMonthIdx(null)}
                      aria-label="Close month view"
                    >
                      ✕
                    </button>
                  </div>

                  <h3 className="modal-title">
                    {CONFIG.ACT_3.chapters[activeMonthIdx].title}
                  </h3>

                  <div className="modal-heart-divider">♡</div>

                  <p className="modal-reflection">
                    "{CONFIG.ACT_3.chapters[activeMonthIdx].reflection}"
                  </p>

                  <div className="modal-learned-box">
                    <span className="learned-label">A tiny thing I learned about you:</span>
                    <p className="learned-text">
                      {CONFIG.ACT_3.chapters[activeMonthIdx].learned}
                    </p>
                  </div>

                  <div className="modal-melody-tag">
                    <span>{CONFIG.ACT_3.chapters[activeMonthIdx].melody}</span>
                  </div>

                  {/* Previous / Next Month Navigation */}
                  <div className="modal-nav-row">
                    <button
                      type="button"
                      className="modal-nav-btn"
                      onClick={() =>
                        setActiveMonthIdx((prev) => (prev > 0 ? prev - 1 : CONFIG.ACT_3.chapters.length - 1))
                      }
                    >
                      ← Previous
                    </button>
                    <span className="modal-counter">
                      Month {activeMonthIdx + 1} of 12
                    </span>
                    <button
                      type="button"
                      className="modal-nav-btn"
                      onClick={() =>
                        setActiveMonthIdx((prev) => (prev < CONFIG.ACT_3.chapters.length - 1 ? prev + 1 : 0))
                      }
                    >
                      Next →
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="act-forward-action">
              <button
                type="button"
                className="grand-romantic-btn"
                onClick={(e) => goToAct(4, e)}
              >
                <span>{CONFIG.ACT_3.nextButton}</span>
              </button>
            </div>
          </section>
        )}

        {/* ===================================================================
            ACT IV — LITTLE VULNERABILITIES & SECRET NOTES
            =================================================================== */}
        {currentAct === 4 && (
          <section className="act-container act-4-vulnerabilities" aria-label="Act 4: Little Vulnerabilities">
            <div className="sacred-badge">
              <span>🌸 ACT IV — HONEST TRUTHS 🌸</span>
            </div>

            <h2 className="section-title">{CONFIG.ACT_4.heading}</h2>
            <p className="section-subtext">{CONFIG.ACT_4.subtext}</p>

            {/* 4 Interactive Vulnerability Cards */}
            <div className="vulnerability-grid">
              {CONFIG.ACT_4.cards.map((c) => {
                const isExpanded = expandedCardId === c.id;
                return (
                  <div
                    key={c.id}
                    className={`vulnerability-card ${isExpanded ? 'expanded' : ''}`}
                    onClick={(e) => {
                      triggerBurst(e.clientX, e.clientY, 8, ['🌸', '💗', '♡']);
                      setExpandedCardId(isExpanded ? null : c.id);
                    }}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => { if (e.key === 'Enter') setExpandedCardId(isExpanded ? null : c.id); }}
                    aria-label={c.title}
                  >
                    <div className="card-top-tag">
                      <span className="tag-pill">{c.tag}</span>
                      <span className="tag-sparkle">✨</span>
                    </div>

                    <h3 className="card-heading">{c.title}</h3>
                    <p className="card-body-text">{c.content}</p>

                    <div className="card-whisper-footer">
                      <span className="whisper-label">whisper:</span>
                      <span className="whisper-val">"{c.whisper}"</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Deep Secret Scratch-to-Reveal Wax Seal */}
            <div className="secret-prayer-box">
              <div className="prayer-top-prompt">
                <span className="prayer-ribbon">💌</span>
                <p>{CONFIG.ACT_4.scratchPrompt}</p>
              </div>

              {!secretRevealed ? (
                <button
                  type="button"
                  className="golden-wax-seal-btn"
                  onClick={(e) => {
                    triggerBurst(e.clientX, e.clientY, 30, ['✨', '🌷', '💗', '🎀', '🧸']);
                    setSecretRevealed(true);
                  }}
                >
                  <span className="seal-emblem">♡</span>
                  <span className="seal-label">TAP TO UNSEAL</span>
                </button>
              ) : (
                <div className="revealed-prayer-card">
                  <div className="prayer-sparkles">✦ 🌸 ✦</div>
                  <p className="prayer-text">{CONFIG.ACT_4.scratchRevealed}</p>
                  <p className="prayer-author">— from lunchbox, with all my heart ♡</p>
                </div>
              )}
            </div>

            <div className="act-forward-action">
              <button
                type="button"
                className="grand-romantic-btn"
                onClick={(e) => goToAct(5, e)}
              >
                <span>{CONFIG.ACT_4.nextButton}</span>
              </button>
            </div>
          </section>
        )}

        {/* ===================================================================
            ACT V — THE CELESTIAL CLIMAX (The "Awe" Moment)
            =================================================================== */}
        {currentAct === 5 && (
          <section className="act-container act-5-climax" aria-label="Act 5: The Celestial Climax">
            <div className="midnight-climax-wrap">
              {/* Beat 1: "AND JUST LIKE THAT..." */}
              <div className={`climax-beat beat-1 ${climaxStep >= 1 ? 'visible' : ''}`}>
                <span className="midnight-badge">{CONFIG.ACT_5.beat1}</span>
                <h1 className="midnight-subtitle">{CONFIG.ACT_5.beat2}</h1>
              </div>

              {/* Beat 2: Hero Climax */}
              {climaxStep >= 2 && (
                <div className="climax-beat beat-2 visible">
                  {/* Glowing Teddy & Heart Centerpiece */}
                  <div
                    className="climax-luminous-mascot"
                    onClick={(e) => triggerBurst(e.clientX, e.clientY, 32)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => { if (e.key === 'Enter') triggerBurst(); }}
                    title="Tap for a magical burst ♡"
                  >
                    <div className="luminous-halo-ring" />
                    <div className="mascot-svg-wrap">
                      <svg viewBox="0 0 120 120" className="mascot-svg">
                        {/* Left Ear */}
                        <circle cx="34" cy="34" r="16" fill="#D3A27F" />
                        <circle cx="34" cy="34" r="9" fill="#F7CAD8" />
                        {/* Right Ear */}
                        <circle cx="86" cy="34" r="16" fill="#D3A27F" />
                        <circle cx="86" cy="34" r="9" fill="#F7CAD8" />
                        {/* Head */}
                        <circle cx="60" cy="55" r="32" fill="#E2B797" />
                        {/* Cheeks */}
                        <circle cx="44" cy="62" r="5" fill="#F9A4BC" opacity="0.6" />
                        <circle cx="76" cy="62" r="5" fill="#F9A4BC" opacity="0.6" />
                        {/* Eyes */}
                        <ellipse cx="48" cy="52" rx="3.5" ry="4.5" fill="#4A3427" />
                        <ellipse cx="72" cy="52" rx="3.5" ry="4.5" fill="#4A3427" />
                        <circle cx="49" cy="50.5" r="1.2" fill="#FFFFFF" />
                        <circle cx="73" cy="50.5" r="1.2" fill="#FFFFFF" />
                        {/* Snout */}
                        <ellipse cx="60" cy="63" rx="11" ry="8" fill="#FFF2E7" />
                        <polygon points="60,61 56,58 64,58" fill="#5A3A29" />
                        <path d="M 57,64 Q 60,67 63,64" stroke="#5A3A29" strokeWidth="1.6" fill="none" strokeLinecap="round" />
                        {/* Glowing Heart */}
                        <path
                          d="M 60,82 C 45,66 28,78 28,94 C 28,107 45,116 60,120 C 75,116 92,107 92,94 C 92,78 75,66 60,82 Z"
                          fill="url(#goldHeartGrad)"
                        />
                        <defs>
                          <linearGradient id="goldHeartGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#FFFFFF" />
                            <stop offset="40%" stopColor="#FF9EB5" />
                            <stop offset="100%" stopColor="#E05B7F" />
                          </linearGradient>
                        </defs>
                        <text x="60" y="103" textAnchor="middle" fill="#FFFFFF" fontSize="11" fontWeight="800" fontFamily="sans-serif">
                          1 YEAR
                        </text>
                      </svg>
                    </div>
                  </div>

                  <h2 className="climax-grand-hero">{CONFIG.ACT_5.hero}</h2>

                  {/* Heartfelt Climax Prose Cards */}
                  <div className="climax-prose-card">
                    {CONFIG.ACT_5.climaxProse.map((line, i) => (
                      <p key={i} className="climax-para">{line}</p>
                    ))}
                  </div>
                </div>
              )}

              {/* Beat 3: Virtual Hug & Keepsake Certificate */}
              {climaxStep >= 3 && (
                <div className="climax-beat beat-3 visible">
                  {/* Hug Interaction */}
                  <div className="hug-interaction-container">
                    {!hugGiven ? (
                      <button
                        type="button"
                        className="grand-romantic-btn hug-special-btn"
                        onClick={(e) => {
                          triggerBurst(e.clientX, e.clientY, 40, ['🫂', '💗', '💋', '🧸', '✨', '🎀', '🌷']);
                          setHugGiven(true);
                        }}
                      >
                        <span>{CONFIG.ACT_5.hugButton}</span>
                      </button>
                    ) : (
                      <div className="hug-delivered-box">
                        <div className="hug-sparkle-row">✨ 💗 🧸 💋 ✨</div>
                        <h3 className="hug-headline">{CONFIG.ACT_5.hugMessage}</h3>
                        <p className="hug-subnote">{CONFIG.ACT_5.hugSub}</p>
                      </div>
                    )}
                  </div>

                  {/* Digital Keepsake Certificate Card */}
                  <div className="keepsake-certificate">
                    <div className="cert-border-corner top-left">✦</div>
                    <div className="cert-border-corner top-right">✦</div>
                    <div className="cert-border-corner bottom-left">✦</div>
                    <div className="cert-border-corner bottom-right">✦</div>

                    <span className="cert-badge">{CONFIG.ACT_5.certificateTitle}</span>
                    <h4 className="cert-names">{CONFIG.HER_NAME} & {CONFIG.MY_NAME}</h4>
                    <p className="cert-label">{CONFIG.ACT_5.certificateDate}</p>
                    <p className="cert-motto">"Even if my English is simple, my love for you is 1000% real."</p>

                    <div className="cert-signature-row">
                      <span>Signed with all my heart,</span>
                      <span className="cert-signature-name">{CONFIG.ACT_5.certificateSign}</span>
                    </div>
                  </div>

                  {/* Replay Option */}
                  <div className="replay-row">
                    <button
                      type="button"
                      className="replay-story-btn"
                      onClick={(e) => {
                        setActiveLetterPage(0);
                        setActiveMonthIdx(null);
                        setExpandedCardId(null);
                        setSecretRevealed(false);
                        setHugGiven(false);
                        goToAct(1, e);
                      }}
                    >
                      {CONFIG.ACT_5.replay}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </section>
        )}
      </main>

      {/* Persistent Warm Footer */}
      <footer className="experience-footer">
        <p>OUR LITTLE UNIVERSE ♡ {CONFIG.ANNIVERSARY_LABEL} • MADE FOR {CONFIG.HER_NAME} BY {CONFIG.MY_NAME}</p>
      </footer>
    </div>
  );
}
