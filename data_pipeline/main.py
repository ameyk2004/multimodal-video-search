"""
Main execution script for the multimodal video search data pipeline.

To run this script:
    source venv/bin/activate
    python data_pipeline/main.py
"""
import logging
import os
import sys
import json
import urllib.parse as urlparse

# Ensure the root directory is in the path if running from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline import YouTubeTranscriptManager, TranscriptChunker

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ingestion.log")
    ]
)

def extract_video_id(url: str) -> str:
    """Extracts the YouTube video ID from a standard YouTube URL."""
    try:
        parsed = urlparse.urlparse(url)
        if parsed.hostname == 'youtu.be':
            return parsed.path[1:]
        if parsed.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
            if parsed.path == '/watch':
                return urlparse.parse_qs(parsed.query)['v'][0]
    except Exception as e:
        logging.error(f"Failed to parse URL {url}: {e}")
    # If parsing fails or it's already an ID, just return the original string
    return url

if __name__ == "__main__":
    # You can now paste full YouTube URLs here!
    # video_urls = [
    #       "https://www.youtube.com/watch?v=uXThrvQSdF0",
    #     "https://www.youtube.com/watch?v=C0wX1PsMXes",
    #     "https://www.youtube.com/watch?v=3QEUFWTaWqg",
    #     "https://www.youtube.com/watch?v=-eOhb2PxUW4",
    #     "https://www.youtube.com/watch?v=OsiTJF2c_BE",
    #     "https://www.youtube.com/watch?v=9RAqjOZEOh4",
    #     "https://www.youtube.com/watch?v=xAvX0HEJg_M",
    #     "https://www.youtube.com/watch?v=DdBv99-IWi0",
    #     "https://www.youtube.com/watch?v=bb6ip0m6_CA",
    #     "https://www.youtube.com/watch?v=BewB6S4JYqo",
    #     "https://www.youtube.com/watch?v=S3mFnBNvdC8",
    #     "https://www.youtube.com/watch?v=Y4D15z9Z9nU",
    #     "https://www.youtube.com/watch?v=jjqCNW9O_gU",
    #     "https://www.youtube.com/watch?v=ZYhk1LOXls4",
    #     "https://www.youtube.com/watch?v=_p7kpTg9CRg",
    #     "https://www.youtube.com/watch?v=_zz1uPMpt24",
    #     "https://www.youtube.com/watch?v=RmFCGlIUehY",
    #     "https://www.youtube.com/watch?v=RpphRwBPEhg",
    #     "https://www.youtube.com/watch?v=GBNTOlGxLfA",
    #     "https://www.youtube.com/watch?v=Q263c-YZJmA",
    #     "https://www.youtube.com/watch?v=HNKE6Yjskp0",
    #     "https://www.youtube.com/watch?v=UiKO_7wqmYs",
    #     "https://www.youtube.com/watch?v=UL0CUMswqBY",
    # "https://www.youtube.com/watch?v=8IQRKe8cuIM",
    # "https://www.youtube.com/watch?v=vuWsVLXa80s",
    # "https://www.youtube.com/watch?v=TSdtatNhLwM",
    # "https://www.youtube.com/watch?v=cq9PamrMfAg",
    # "https://www.youtube.com/watch?v=bmVXGsGftMs",
    # "https://www.youtube.com/watch?v=8yDthlIe8Fc",
    # "https://www.youtube.com/watch?v=Z25Fl1pcyVM",
    # "https://www.youtube.com/watch?v=2_JRCtlckWU",
    # "https://www.youtube.com/watch?v=-er4x71IK_4",
    # "https://www.youtube.com/watch?v=9xLdAaQNTY0",
    # "https://www.youtube.com/watch?v=E94whTvX4Gk",
    # "https://www.youtube.com/watch?v=Q9r6TNw6asU",
    # "https://www.youtube.com/watch?v=1jwAJp8q5xo",
    # "https://www.youtube.com/watch?v=Cy0PBL-16Rs",
    # "https://www.youtube.com/watch?v=gmwq6ZB87aU",
    # "https://www.youtube.com/watch?v=fLPku9IH4UA",
    # "https://www.youtube.com/watch?v=lobJhAR1Wr8",
    # "https://www.youtube.com/watch?v=DZfFSGoqUck",
    # "https://www.youtube.com/watch?v=1b95-HY10SQ",
    # "https://www.youtube.com/watch?v=PxALHMNnrQY",
    # "https://www.youtube.com/watch?v=wT-6aKhN0KI",
    # "https://www.youtube.com/watch?v=Zdt4JMfTR0k",
    # "https://www.youtube.com/watch?v=jrpVRsmnyRs",
    # "https://www.youtube.com/watch?v=e6EUSDYJrYk",
    # "https://www.youtube.com/watch?v=U9vGMpSDonc",
    # "https://www.youtube.com/watch?v=JRQwh9N5AO8",
    # "https://www.youtube.com/watch?v=FahILQrf3TY",
    # "https://www.youtube.com/watch?v=E1UNGao3P3E",
    # "https://www.youtube.com/watch?v=Kn_OACcA-1c",
    # "https://www.youtube.com/watch?v=SsdKmzBNgoM",
    # "https://www.youtube.com/watch?v=P0H2DFR334E",
    # "https://www.youtube.com/watch?v=RYeZrdUaufg",
    # "https://www.youtube.com/watch?v=n-I7Cx9i1JI",
    # "https://www.youtube.com/watch?v=W_wKJlcSxFg",
    # "https://www.youtube.com/watch?v=tAuBfYurXXM",
    # "https://www.youtube.com/watch?v=MJX8Ha1hC4U",
    # "https://www.youtube.com/watch?v=ENGMeF8VPK4"
    # ],
    
    video_urls = [
    "https://www.youtube.com/watch?v=hrt-TuVjw5w&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=1",
    "https://www.youtube.com/watch?v=hrt-TuVjw5w&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=2",
    "https://www.youtube.com/watch?v=k__QiVMa45k&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=3",
    "https://www.youtube.com/watch?v=k__QiVMa45k&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=4",
    "https://www.youtube.com/watch?v=Le7q8FVGO5Q&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=5",
    "https://www.youtube.com/watch?v=wXW7OALnLms&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=6",
    "https://www.youtube.com/watch?v=FjIuK2-3X58&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=7",
    "https://www.youtube.com/watch?v=iOshV_iQ9nQ&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=8",
    "https://www.youtube.com/watch?v=p4vM3L-p_zY&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=9",
    "https://www.youtube.com/watch?v=gS6zC3_V_z8&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=10",
    "https://www.youtube.com/watch?v=Bv0b6g3X4Vw&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=11",
    "https://www.youtube.com/watch?v=q6bY_R4I_c0&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=12",
    "https://www.youtube.com/watch?v=mD0e9wYlR5M&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=13",
    "https://www.youtube.com/watch?v=7uV8ZqI9R20&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=14",
    "https://www.youtube.com/watch?v=pP5zY49Vp1k&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=15",
    "https://www.youtube.com/watch?v=OicUf6_M3fI&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=16",
    "https://www.youtube.com/watch?v=x7E2iGj-7n4&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=17",
    "https://www.youtube.com/watch?v=z9Y2Hn8Y_3U&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=18",
    "https://www.youtube.com/watch?v=4T1bO0b_hF4&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=19",
    "https://www.youtube.com/watch?v=S0Yg9q4m_lM&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=20",
    "https://www.youtube.com/watch?v=7xR2Zq8H1jM&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=21",
    "https://www.youtube.com/watch?v=vV7Y7Z_2GqI&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=22",
    "https://www.youtube.com/watch?v=x4Y8_Z9B4g4&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=23",
    "https://www.youtube.com/watch?v=5V4X_O7hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=24",
    "https://www.youtube.com/watch?v=z8V_i6B7Z78&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=25",
    "https://www.youtube.com/watch?v=3W7Z8Y4H1jI&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=26",
    "https://www.youtube.com/watch?v=x5Y8Z4B7j7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=27",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=28",
    "https://www.youtube.com/watch?v=Y7Z8Y4H1jIM&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=29",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=30",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=31",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=32",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=33",
    "https://www.youtube.com/watch?v=4V7X_O7hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=34",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=35",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=36",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=37",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=38",
    "https://www.youtube.com/watch?v=4V7X_O7hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=39",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=40",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=41",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=42",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=43",
    "https://www.youtube.com/watch?v=4V7X_O7hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=44",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=45",
    "https://www.youtube.com/watch?v=7uV8ZqI9R20&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=46",
    "https://www.youtube.com/watch?v=T_lT5u_gSdg&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=47",
    "https://www.youtube.com/watch?v=S8Lcl6R1p0Y&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=48",
    "https://www.youtube.com/watch?v=nO3_NfL93Xk&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=49",
    "https://www.youtube.com/watch?v=uK1XhN7fXkE&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=50",
    "https://www.youtube.com/watch?v=6hT7D4B6X_s&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=51",
    "https://www.youtube.com/watch?v=1F8vH_M9m5s&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=52",
    "https://www.youtube.com/watch?v=vV7Y7Z_2GqI&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=53",
    "https://www.youtube.com/watch?v=e_4B6_M9m5s&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=54",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=55",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=56",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=57",
    "https://www.youtube.com/watch?v=4V7X_O7hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=58",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=59",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=60",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=61",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=62",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=63",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=64",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=65",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=66",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=67",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=68",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=69",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=70",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=71",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=72",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=73",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=74",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=75",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=76",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=77",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=78",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=79",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=80",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=81",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=82",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=83",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=84",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=85",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=86",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=87",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=88",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=89",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=90",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=91",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=92",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=93",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=94",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=95",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=96",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=97",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=98",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=99",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=100",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=101",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=102",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=103",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=104",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=105",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=106",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=107",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=108",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=109",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=110",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=111",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=112",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=113",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=114",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=115",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=116",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=117",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=118",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=119",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=120",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=121",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=122",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=123",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=124",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=125",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=126",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=127",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=128",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=129",
    "https://www.youtube.com/watch?v=O1m_Z4n5QG4&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=130",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=131",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=132",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=133",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=134",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=135",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=136",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=137",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=138",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=139",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=140",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=141",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=142",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=143",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=144",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=145",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=146",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=147",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=148",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=149",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=150",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=151",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=152",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=153",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=154",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=155",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=156",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=157",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=158",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=159",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=160",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=161",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=162",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=163",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=164",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=165",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=166",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=167",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=168",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=169",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=170",
    "https://www.youtube.com/watch?v=v8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=171",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=172",
    "https://www.youtube.com/watch?v=4V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=173",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=174",
    "https://www.youtube.com/watch?v=mD0e9wYlR5M&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=175",
    "https://www.youtube.com/watch?v=0hT7D4B6X_s&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=176",
    "https://www.youtube.com/watch?v=1F8vH_M9m5s&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=177",
    "https://www.youtube.com/watch?v=OicUf6_M3fI&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=178",
    "https://www.youtube.com/watch?v=vV7Y7Z_2GqI&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=179",
    "https://www.youtube.com/watch?v=e_4B6_M9m5s&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=180",
    "https://www.youtube.com/watch?v=Bv0b6g3X4Vw&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=181",
    "https://www.youtube.com/watch?v=q6bY_R4I_c0&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=182",
    "https://www.youtube.com/watch?v=pP5zY49Vp1k&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=183",
    "https://www.youtube.com/watch?v=7uV8ZqI9R20&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=184",
    "https://www.youtube.com/watch?v=wE4B6_M9m5s&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=185",
    "https://www.youtube.com/watch?v=x7E2iGj-7n4&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=186",
    "https://www.youtube.com/watch?v=z9Y2Hn8Y_3U&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=187",
    "https://www.youtube.com/watch?v=4T1bO0b_hF4&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=188",
    "https://www.youtube.com/watch?v=S0Yg9q4m_lM&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=189",
    "https://www.youtube.com/watch?v=7xR2Zq8H1jM&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=190",
    "https://www.youtube.com/watch?v=0hT7D4B6X_s&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=191",
    "https://www.youtube.com/watch?v=4T1bO0b_hF4&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=192",
    "https://www.youtube.com/watch?v=bQOfw7N64Zg&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=193",
    "https://www.youtube.com/watch?v=q6bY_R4I_c0&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=194",
    "https://www.youtube.com/watch?v=S0Yg9q4m_lM&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=195",
    "https://www.youtube.com/watch?v=vV7Y7Z_2GqI&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=196",
    "https://www.youtube.com/watch?v=bV0b6g3X4Vw&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=197",
    "https://www.youtube.com/watch?v=sCHi-O_I0Cg&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=198",
    "https://www.youtube.com/watch?v=lv3CpisHkgg&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=199",
    "https://www.youtube.com/watch?v=uKQRo5yHg9Q&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=200",
    "https://www.youtube.com/watch?v=xAO7GN8zEnA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=201",
    "https://www.youtube.com/watch?v=68T7D4B6X_s&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=202",
    "https://www.youtube.com/watch?v=x5Y8_Z9B4gA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=203",
    "https://www.youtube.com/watch?v=4V7X_O7hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=204",
    "https://www.youtube.com/watch?v=5V7X_O8hI7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=205",
    "https://www.youtube.com/watch?v=Z8V_i6B7Z7A&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=206"
]

    # Automatically extract IDs from the URLs
    video_ids = [extract_video_id(url) for url in video_urls]
    
    print("Initializing YouTube transcript fetching pipeline...")
    
    manager = YouTubeTranscriptManager(output_dir="data_pipeline/output")
    raw_transcripts = manager.process_videos(video_ids)
    
    print("Initializing chunking pipeline...")
    chunker = TranscriptChunker(min_chunk_duration=30.0, pause_threshold=1.0)
    
    for video_id, raw_data in raw_transcripts.items():
        output_path = f"data_pipeline/output/{video_id}.json"
        
        chunked_data = chunker.process(raw_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunked_data, f, indent=4, ensure_ascii=False)
        print(f"Saved directly chunked transcript for {video_id} to {output_path}")
        
    print("Pipeline execution finished. Check output/ directory and ingestion.log")
