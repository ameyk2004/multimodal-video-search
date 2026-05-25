import React, { useState, useEffect } from 'react';
import RelatedQuestions from './RelatedQuestions';
import './SearchGreeting.css';

const FALLBACK_QUERIES = [
  "नामस्मरण कसे करावे?",
  "संसारात राहून परमार्थ कसा साधावा?",
  "ध्यानाची योग्य पद्धत कोणती?",
  "मन एकाग्र कसे करावे?",
  "संत तुकारामांच्या अभंगांचा अर्थ काय?",
  "अहंकार कसा नष्ट करावा?",
  "सद्गुरूंचे महत्त्व काय आहे?",
  "जीवनात शांती कशी मिळवावी?",
  "नामस्मरणाचे फायदे काय आहेत?",
  "श्री पेठे काकांचे विचार काय आहेत?",
  "भक्ती म्हणजे काय?",
  "स्वतःची ओळख कशी करून घ्यावी?",
  "संकटांना धैर्याने कसे सामोरे जावे?",
  "कर्म आणि फळ यात काय संबंध आहे?",
  "आत्मज्ञानाची प्राप्ती कशी होते?"
];

const Typewriter = ({ text, delay = 30 }) => {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    setIndex(0);
    const timer = setInterval(() => {
      setIndex((prev) => {
        if (prev < text.length) {
          return prev + 1;
        }
        clearInterval(timer);
        return prev;
      });
    }, delay);
    return () => clearInterval(timer);
  }, [text, delay]);

  return <span>{text.substring(0, index)}</span>;
};

export default function SearchGreeting({ onSearch, lang }) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    // Sequence animations: 1 second between each step
    const t1 = setTimeout(() => setStep(1), 300);  // Show msg 1
    const t2 = setTimeout(() => setStep(2), 1500); // Show msg 2 (starts typing after msg 1)
    const t3 = setTimeout(() => setStep(3), 3500); // Show RelatedQuestions
    
    return () => { 
      clearTimeout(t1); 
      clearTimeout(t2); 
      clearTimeout(t3); 
    };
  }, []);

  return (
    <div className="search-greeting-container">
       {step >= 1 && (
         <div className="sg-message">
           <span className="sg-icon">🙏</span>
           <span className="sg-text">
             <Typewriter text="नमस्कार साधक!" delay={40} />
           </span>
         </div>
       )}
       
       {step >= 2 && (
         <div className="sg-message">
           <span className="sg-text">
             <Typewriter text="आज तुम्हाला तुमच्या कोणत्या शंकेचे निवारण करायचे आहे?" delay={35} />
           </span>
         </div>
       )}
       
       {step >= 3 && (
         <div className="sg-questions-wrapper">
            <RelatedQuestions 
              metadata={null} 
              fallbackQueries={FALLBACK_QUERIES} 
              onSearch={onSearch} 
              lang={lang} 
              customTitle="थेट प्रश्न विचारा" 
            />
         </div>
       )}
    </div>
  );
}
