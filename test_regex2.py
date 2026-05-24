import re
import string

full_text = 'आपल्याला मागे आपण वाचलं असेल ॲनिमल कादंबरी वाचली असेल किंवा हे वाचलं असेल त्यांना माहिती असेल की असं'
start_text = 'आपल्याला मागे आपण वाचलं असेल निमल कादंबरी वाचली असेल किंवा हे वाचलं असेल त्यांना माहिती असेल की असं ...'

def fuzzy_find(start_text, full_text):
    words = start_text.split()
    clean_words = [w.strip(string.punctuation) for w in words if w.strip(string.punctuation)]
    
    if not clean_words:
        return -1
        
    # Generate patterns from strict to loose
    # We'll try sequences of lengths 15, 10, 7, 5, 3
    # And we'll try offsets: start at word 0, or word 1 (in case first word is hallucinated)
    
    for length in [15, 10, 7, 5, 3]:
        for offset in [0, 1, 2]:
            if offset + length <= len(clean_words):
                pattern_words = clean_words[offset : offset + length]
                # join with wildcard for whitespace/punctuation
                pattern = r'[\s,.\?!;:\"\'\-]+'.join(re.escape(w) for w in pattern_words)
                
                # To make sure we match word boundaries and not inside a word, we could add \b but \b is tricky with Marathi.
                # We can just search.
                match = re.search(pattern, full_text)
                if match:
                    # We want the start of the MATCH. But wait, if offset > 0, the match starts at word 1, not word 0!
                    # That means our timestamp will be slightly off (by 1 word). That's perfectly fine! 1 word is like 0.3 seconds.
                    return match.start()
                    
    return -1

print('Match at:', fuzzy_find(start_text, full_text))

