import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import logo from '../assets/images/sadhanandadeep_logo.webp';
import './HomePage.css';
import pethekaka from '../assets/images/pethekaka.png';

const fadeUp = {
  hidden: { opacity: 0, y: 60 },
  visible: (delay = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.9, delay, ease: [0.22, 1, 0.36, 1] },
  }),
};

const stagger = {
  visible: { transition: { staggerChildren: 0.15 } },
};

export default function HomePage({ t, lang, allVideos, onSearch }) {
  const navigate = useNavigate();

  const featuredVideos =
    allVideos && allVideos.length > 0 ? allVideos.slice(0, 6) : [];

  return (
    <div className="hp">
      {/* ─── HERO ─────────────────────────────────────────── */}
      <section className="hp-hero">
        {/* Ambient glow */}
        <div className="hp-hero__glow" />

        <motion.div
          className="hp-hero__inner"
          initial="hidden"
          animate="visible"
          variants={stagger}
        >
          <motion.img
            src={logo}
            alt="Sadhananandadeep"
            className="hp-hero__logo"
            variants={fadeUp}
            custom={0}
          />

          <motion.h1 className="hp-hero__title" variants={fadeUp} custom={0.15}>
            {t.title}
          </motion.h1>

          <motion.p className="hp-hero__sub" variants={fadeUp} custom={0.3}>
            {t.subtitle}
          </motion.p>

          <motion.div className="hp-hero__cta" variants={fadeUp} custom={0.45}>
            <button
              className="hp-btn hp-btn--primary"
              onClick={() => navigate('/search')}
            >
              <span>✧</span>
              {lang === 'mr' ? 'ज्ञानकोश शोधा' : 'Explore Knowledge Base'}
            </button>
            <button
              className="hp-btn hp-btn--outline"
              onClick={() => navigate('/stories')}
            >
              {t.storiesTab}
            </button>
          </motion.div>
        </motion.div>

        <motion.div
          className="hp-hero__scroll"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.7 }}
          transition={{ delay: 1.8, duration: 1 }}
        >
          <div className="hp-scroll-mouse">
            <div className="hp-scroll-wheel"></div>
          </div>
        </motion.div>
      </section>

      {/* ─── ABOUT ────────────────────────────────────────── */}
      <section className="hp-section">
        <motion.div
          className="hp-about"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.25 }}
          variants={stagger}
        >
          <motion.div className="hp-about__img-col" variants={fadeUp}>
            <div className="hp-portrait">
              <div className="hp-portrait__ring" />
              <img src={pethekaka} alt="Shree Pethe Kaka" />
            </div>
          </motion.div>

          <motion.div className="hp-about__text-col" variants={fadeUp} custom={0.2}>
            <span className="hp-label">
              {lang === 'mr' ? 'परिचय' : 'Introduction'}
            </span>
            <h2 className="hp-heading">
              {lang === 'mr' ? 'श्री काकांविषयी…' : 'About Shree Kaka…'}
            </h2>
            <p className="hp-body">{t.bio}</p>
          </motion.div>
        </motion.div>
      </section>

      {/* ─── YOUTUBE ──────────────────────────────────────── */}
      <section className="hp-section hp-section--dark">
        <motion.div
          className="hp-yt"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          variants={stagger}
        >
          <motion.div className="hp-yt__text-col" variants={fadeUp}>
            <span className="hp-label">YouTube</span>
            <h2 className="hp-heading">
              {lang === 'mr' ? 'अधिकृत YouTube चॅनेल' : 'Official YouTube Channel'}
            </h2>
            <p className="hp-body">
              {lang === 'mr'
                ? 'श्री काकांच्या सर्व प्रवचनांचे, अभंगांचे आणि आरत्यांचे व्हिडिओ पाहण्यासाठी आमच्या अधिकृत YouTube चॅनेलला भेट द्या. नवीन शिकवणींचे व्हिडिओ नियमितपणे प्रकाशित होतात.'
                : 'Watch all discourses, abhangs, and aartis by Shree Kaka on our official YouTube channel. New teachings are published regularly.'}
            </p>
            <a
              href="https://www.youtube.com/@shripethekaka8327"
              target="_blank"
              rel="noreferrer"
              className="hp-btn hp-btn--yt"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
              </svg>
              {lang === 'mr' ? 'चॅनेलला भेट द्या' : 'Visit Channel'}
            </a>
          </motion.div>
        </motion.div>
      </section>

      {/* ─── FEATURED VIDEOS ──────────────────────────────── */}
      {featuredVideos.length > 0 && (
        <section className="hp-section">
          <motion.div
            className="hp-videos"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.15 }}
            variants={stagger}
          >
            <motion.div className="hp-videos__header" variants={fadeUp}>
              <span className="hp-label">
                {lang === 'mr' ? 'प्रवचने' : 'Discourses'}
              </span>
              <h2 className="hp-heading">
                {lang === 'mr'
                  ? 'नवीनतम शिकवणी'
                  : 'Latest Teachings'}
              </h2>
            </motion.div>

            <motion.div className="hp-videos__grid" variants={fadeUp} custom={0.15}>
              {featuredVideos.map((v, i) => (
                <div
                  key={v.video_id || i}
                  className="hp-vcard"
                  onClick={() => navigate('/library')}
                >
                  <div className="hp-vcard__thumb">
                    <img
                      src={`https://img.youtube.com/vi/${v.video_id}/mqdefault.jpg`}
                      alt="Video"
                      onError={(e) => {
                        e.target.src = `https://img.youtube.com/vi/${v.video_id}/hqdefault.jpg`;
                      }}
                    />
                    <div className="hp-vcard__play">▶</div>
                  </div>
                  <div className="hp-vcard__body">
                    <h4>{v.title || (lang === 'mr' ? 'प्रवचन' : 'Discourse')}</h4>
                    <span>
                      {v.topic_count || 0} {lang === 'mr' ? 'विषय' : 'Topics'}
                      {v.query_count ? ` · ${v.query_count} ${lang === 'mr' ? 'प्रश्न' : 'Queries'}` : ''}
                    </span>
                  </div>
                </div>
              ))}
            </motion.div>

            <motion.div className="hp-videos__more" variants={fadeUp} custom={0.3}>
              <button
                className="hp-btn hp-btn--outline"
                onClick={() => navigate('/library')}
              >
                {lang === 'mr' ? 'सर्व प्रवचने पहा' : 'View All Discourses'} →
              </button>
            </motion.div>
          </motion.div>
        </section>
      )}

      {/* ─── APP DOWNLOAD ─────────────────────────────────── */}
      <section className="hp-section hp-section--dark">
        <motion.div
          className="hp-app"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          variants={stagger}
        >
          <motion.div className="hp-app__content" variants={fadeUp}>
            <span className="hp-label">
              {lang === 'mr' ? 'मोबाईल ॲप' : 'Mobile App'}
            </span>
            <h2 className="hp-heading">
              {lang === 'mr'
                ? 'साधननंदादीप ॲप डाऊनलोड करा'
                : 'Download the Sadhananandadeep App'}
            </h2>
            <p className="hp-body">
              {lang === 'mr'
                ? 'तुमच्या मोबाईलवर कधीही, कुठेही अभंग, आरत्या, श्लोक आणि चिंतने ऐका. हे ॲप सर्व जिज्ञासू साधकांसाठी पूर्णपणे विनामूल्य आहे. ७५ पुस्तकांचा, नित्यपाठांचा आणि शेकडो रचनांचा संपूर्ण संग्रह आपल्या बोटांच्या टोकावर.'
                : 'Listen to abhangs, aartis, shlokas and meditations anytime, anywhere. This app is completely free for all seekers. The complete collection of 75 books, daily prayers, and hundreds of compositions — at your fingertips.'}
            </p>
            <a
              href="https://play.google.com/store/apps/details?id=com.pethekaka"
              target="_blank"
              rel="noreferrer"
              className="hp-playstore"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3.609 1.814L13.792 12 3.61 22.186a2.18 2.18 0 0 1-.109-.688V2.502c0-.239.038-.47.109-.688z" fill="#4285F4"/>
                <path d="M17.727 8.056L5.051.674A2.148 2.148 0 0 0 3.609 1.814L13.792 12l3.935-3.944z" fill="#EA4335"/>
                <path d="M3.609 22.186A2.15 2.15 0 0 0 5.05 23.326l12.677-7.382L13.792 12 3.609 22.186z" fill="#34A853"/>
                <path d="M21.743 10.358l-4.016-2.302L13.792 12l3.935 3.944 4.016-2.302c.775-.452 1.257-1.275 1.257-2.142s-.482-1.69-1.257-2.142z" fill="#FBBC04"/>
              </svg>
              <div className="hp-playstore__text">
                <small>{lang === 'mr' ? 'यावर उपलब्ध' : 'GET IT ON'}</small>
                <strong>Google Play</strong>
              </div>
            </a>
          </motion.div>

          <motion.div className="hp-app__visual" variants={fadeUp} custom={0.2}>
            <div className="hp-phone">
              <div className="hp-phone__screen">
                <img src={logo} alt="App" />
                <span className="hp-phone__appname">{t.title}</span>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* ─── FOOTER ───────────────────────────────────────── */}
      <footer className="hp-footer">
        <div className="hp-footer__inner">
          <img src={logo} alt="Logo" className="hp-footer__logo" />
          <p>
            {lang === 'mr'
              ? '© श्री पेठेकाका · साधननंदादीप · सातारा, महाराष्ट्र'
              : '© Shree Pethe Kaka · Sadhananandadeep · Satara, Maharashtra'}
          </p>
          <div className="hp-footer__links">
            <a href="https://www.youtube.com/@shripethekaka8327" target="_blank" rel="noreferrer">YouTube</a>
            <a href="https://play.google.com/store/apps/details?id=com.pethekaka" target="_blank" rel="noreferrer">Google Play</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
