import React, { useState, useRef } from 'react';
import './Library.css';

export default function BookLibraryCard({ book, onClick }) {
  const [imageError, setImageError] = useState(false);
  const [isOpening, setIsOpening] = useState(false);
  const cardRef = useRef(null);
  const coverUrl = `/books/${book.title}.jpg`;

  const handleClick = () => {
    setIsOpening(true);
    // Let the opening animation play, then trigger the panel
    setTimeout(() => {
      onClick(book.title);
      // Reset after panel takes over
      setTimeout(() => setIsOpening(false), 100);
    }, 600);
  };

  return (
    <div
      ref={cardRef}
      className={`book-library-card ${isOpening ? 'book-opening' : ''}`}
      onClick={handleClick}
    >
      {/* Stacked pages behind the cover */}
      <div className="book-pages-stack">
        <div className="book-page page-1"></div>
        <div className="book-page page-2"></div>
        <div className="book-page page-3"></div>
        <div className="book-page page-4"></div>
      </div>

      {/* The cover that opens */}
      <div className="book-card-cover" style={!imageError ? { padding: 0, background: 'none' } : {}}>
        {!imageError && (
          <img
            src={coverUrl}
            alt={book.title}
            className="book-card-thumb"
            onError={() => setImageError(true)}
          />
        )}
        {imageError && (
          <>
            <div className="book-spine"></div>
            <div className="book-cover-content">
              <span className="book-icon">📖</span>
              <h3 className="book-cover-title">{book.title}</h3>
              <p className="book-cover-author">{book.author}</p>
            </div>
          </>
        )}
      </div>

      {/* Bottom meta */}
      <div className="book-card-meta-bottom">
        <div className="book-card-stats">
          <span>{book.topics?.length || 0} Topics</span>
          <span className="meta-dot">•</span>
          <span>{book.questions?.length || book.question_count || 0} Questions</span>
        </div>
      </div>
    </div>
  );
}
