import subprocess

result = subprocess.run(
    [
        "yt-dlp",
        "--flat-playlist",
        "--print", "%(id)s|||%(upload_date)s",
        "https://youtube.com/playlist?list=PLS0pq2M-6hSLMTdf3h2E6BfcAXiPY4Cak"
    ],
    capture_output=True, text=True
)

urls = []
for line in result.stdout.strip().split("\n"):
    video_id, upload_date = line.split("|||")
    if upload_date and upload_date != "NA" and int(upload_date[:4]) > 2014:
        urls.append(f"https://www.youtube.com/watch?v={video_id}")

print(urls)