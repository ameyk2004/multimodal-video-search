import re

full_text = "मी तंबाखू पिकू शकतो मी गहू पण पिकू शकतो"
start_text = "मी तंबाखू पिकू शकतो, मी गहू पण पिकू शकतो...."

words = [w for w in re.split(r'\W+', start_text) if w]
pattern = r'\W+'.join(re.escape(w) for w in words[:15]) # take up to 15 words
print("Pattern:", pattern)

match = re.search(pattern, full_text)
if match:
    print("Match at:", match.start(), match.group())
else:
    print("No match")

