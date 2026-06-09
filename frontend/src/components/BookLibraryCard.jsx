import React from 'react';
import './Library.css';

export default function BookLibraryCard({ book, onClick }) {
  return (
    <div className="book-library-card" onClick={() => onClick(book.title)}>
      <div className="book-card-cover">
        <div className="book-spine"></div>
        <div className="book-cover-content">
          <span className="book-icon">📖</span>
          <h3 className="book-cover-title">{book.title}</h3>
          <p className="book-cover-author">{book.author}</p>
        </div>
        <div className="book-card-overlay">
          <div className="read-overlay">
            <div className="read-text">वाचा (Read)</div>
          </div>
        </div>
      </div>
      <div className="book-card-meta-bottom">
        <div className="book-card-stats">
          <span>{book.topics?.length || 0} Topics</span>
          <span className="meta-dot">•</span>
          <span>{book.question_count || 0} Questions</span>
        </div>
        {book.mood && <div className="book-card-mood">{book.mood}</div>}
      </div>
    </div>
  );
}
