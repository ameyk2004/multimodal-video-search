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
    video_urls = [
    "https://www.youtube.com/watch?v=uXThrvQSdF0",
        "https://www.youtube.com/watch?v=C0wX1PsMXes",
        "https://www.youtube.com/watch?v=3QEUFWTaWqg",
        "https://www.youtube.com/watch?v=-eOhb2PxUW4",
        "https://www.youtube.com/watch?v=OsiTJF2c_BE",
        "https://www.youtube.com/watch?v=9RAqjOZEOh4",
        "https://www.youtube.com/watch?v=xAvX0HEJg_M",
    "https://www.youtube.com/watch?v=DdBv99-IWi0",
    "https://www.youtube.com/watch?v=bb6ip0m6_CA",
    "https://www.youtube.com/watch?v=BewB6S4JYqo",
    "https://www.youtube.com/watch?v=S3mFnBNvdC8",
    "https://www.youtube.com/watch?v=Y4D15z9Z9nU",
    "https://www.youtube.com/watch?v=jjqCNW9O_gU",
    "https://www.youtube.com/watch?v=ZYhk1LOXls4",
    "https://www.youtube.com/watch?v=_p7kpTg9CRg",
    "https://www.youtube.com/watch?v=_zz1uPMpt24",
    "https://www.youtube.com/watch?v=RmFCGlIUehY",
    "https://www.youtube.com/watch?v=RpphRwBPEhg",
    "https://www.youtube.com/watch?v=GBNTOlGxLfA",
    "https://www.youtube.com/watch?v=Q263c-YZJmA",
    "https://www.youtube.com/watch?v=HNKE6Yjskp0",
    "https://www.youtube.com/watch?v=UiKO_7wqmYs",
    "https://www.youtube.com/watch?v=UL0CUMswqBY",
    "https://www.youtube.com/watch?v=8IQRKe8cuIM",
    "https://www.youtube.com/watch?v=vuWsVLXa80s",
    "https://www.youtube.com/watch?v=TSdtatNhLwM",
    "https://www.youtube.com/watch?v=cq9PamrMfAg",
    "https://www.youtube.com/watch?v=bmVXGsGftMs",
    "https://www.youtube.com/watch?v=8yDthlIe8Fc",
    "https://www.youtube.com/watch?v=Z25Fl1pcyVM",
    "https://www.youtube.com/watch?v=2_JRCtlckWU",
    "https://www.youtube.com/watch?v=-er4x71IK_4",
    "https://www.youtube.com/watch?v=9xLdAaQNTY0",
    "https://www.youtube.com/watch?v=E94whTvX4Gk",
    "https://www.youtube.com/watch?v=Q9r6TNw6asU",
    "https://www.youtube.com/watch?v=1jwAJp8q5xo",
    "https://www.youtube.com/watch?v=Cy0PBL-16Rs",
    "https://www.youtube.com/watch?v=gmwq6ZB87aU",
    "https://www.youtube.com/watch?v=fLPku9IH4UA",
    "https://www.youtube.com/watch?v=lobJhAR1Wr8",
    "https://www.youtube.com/watch?v=DZfFSGoqUck",
    "https://www.youtube.com/watch?v=1b95-HY10SQ",
    "https://www.youtube.com/watch?v=PxALHMNnrQY",
    "https://www.youtube.com/watch?v=wT-6aKhN0KI",
    "https://www.youtube.com/watch?v=Zdt4JMfTR0k",
    "https://www.youtube.com/watch?v=jrpVRsmnyRs",
    "https://www.youtube.com/watch?v=e6EUSDYJrYk",
    "https://www.youtube.com/watch?v=U9vGMpSDonc",
    "https://www.youtube.com/watch?v=JRQwh9N5AO8",
    "https://www.youtube.com/watch?v=FahILQrf3TY",
    "https://www.youtube.com/watch?v=E1UNGao3P3E",
    "https://www.youtube.com/watch?v=Kn_OACcA-1c",
    "https://www.youtube.com/watch?v=SsdKmzBNgoM",
    "https://www.youtube.com/watch?v=P0H2DFR334E",
    "https://www.youtube.com/watch?v=RYeZrdUaufg",
    "https://www.youtube.com/watch?v=n-I7Cx9i1JI",
    "https://www.youtube.com/watch?v=W_wKJlcSxFg",
    "https://www.youtube.com/watch?v=tAuBfYurXXM",
    "https://www.youtube.com/watch?v=MJX8Ha1hC4U",
    "https://www.youtube.com/watch?v=ENGMeF8VPK4",
    "https://www.youtube.com/watch?v=J3eXEj4mafg&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=98",
    "https://www.youtube.com/watch?v=h6dO0OEnhek&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=99",
    "https://www.youtube.com/watch?v=5dC75vFmm-g&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=100",
    "https://www.youtube.com/watch?v=YuqvJuXrstU&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=101",
    "https://www.youtube.com/watch?v=cibj2v39GUc&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=102",
    "https://www.youtube.com/watch?v=hMdvSTUuvww&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=103",
    "https://www.youtube.com/watch?v=VRpNjpOx6_8&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=104",
    "https://www.youtube.com/watch?v=2-B2_2tSfBw&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=105",
    "https://www.youtube.com/watch?v=swFveVlCZgA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=106",
    "https://www.youtube.com/watch?v=Z2er2Nnne54&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=107",
    "https://www.youtube.com/watch?v=nN_hffL4vL4&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=108",
    "https://www.youtube.com/watch?v=F1R2JwbFOf8&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=109",
    "https://www.youtube.com/watch?v=BzByk29NyAE&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=110",
    "https://www.youtube.com/watch?v=aK_qjCIBHI0&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=111",
    "https://www.youtube.com/watch?v=0Nx64EOI0m4&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=112",
    "https://www.youtube.com/watch?v=eRe91bfUpik&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=113",
    "https://www.youtube.com/watch?v=rzTkJ1quM8o&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=114",
    "https://www.youtube.com/watch?v=q9FWq5hb_f8&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=115",
    "https://www.youtube.com/watch?v=J-J9ttT2eDg&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=116",
    "https://www.youtube.com/watch?v=FEeRAw52Oek&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=117",
    "https://www.youtube.com/watch?v=G1LbW-H6M1k&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=118",
    "https://www.youtube.com/watch?v=mopz5wnA3PQ&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=119",
    "https://www.youtube.com/watch?v=q_sI7-kB3ag&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=120",
    "https://www.youtube.com/watch?v=NZF0y8n_T9w&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=121",
    "https://www.youtube.com/watch?v=MFGmu32RrKM&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=122",
    "https://www.youtube.com/watch?v=4Yw-6F59jto&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=123",
    "https://www.youtube.com/watch?v=7_L-UkiON0o&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=124",
    "https://www.youtube.com/watch?v=lm-zwgzxxKw&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=125",
    "https://www.youtube.com/watch?v=Repzts-m-Cs&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=126",
    "https://www.youtube.com/watch?v=6y1_0EbqYmg&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=127",
    "https://www.youtube.com/watch?v=qaiyVJ5lGKk&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=128",
    "https://www.youtube.com/watch?v=V6nGe0qzTh0&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=129",
    "https://www.youtube.com/watch?v=5iXGWBwbOC8&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=130",
    "https://www.youtube.com/watch?v=iDCt6E-tNWE&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=131",
    "https://www.youtube.com/watch?v=rPdFlBKC6Vg&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=132",
    "https://www.youtube.com/watch?v=q3Yu47_wjXc&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=133",
    "https://www.youtube.com/watch?v=5XASMT72YJo&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=134",
    "https://www.youtube.com/watch?v=jpOJBKYCIRU&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=135",
    "https://www.youtube.com/watch?v=A9wGK4kyIiA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=136",
    "https://www.youtube.com/watch?v=b1dTnfN9ebA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=137",
    "https://www.youtube.com/watch?v=ipp2CsOpSXQ&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=138",
    "https://www.youtube.com/watch?v=l_PNBPSvI_c&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=139",
    "https://www.youtube.com/watch?v=4pNO68OkTWA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=140",
    "https://www.youtube.com/watch?v=IzpkxlVb4OE&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=141",
    "https://www.youtube.com/watch?v=bK_oRmmB6Aw&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=142",
    "https://www.youtube.com/watch?v=tp1tGTU9c7s&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=143",
    "https://www.youtube.com/watch?v=ka24gzw7J0U&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=144",
    "https://www.youtube.com/watch?v=skRs4n9crGo&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=145",
    "https://www.youtube.com/watch?v=49Mp9553L7o&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=146",
    "https://www.youtube.com/watch?v=rzORPFudK8M&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=147",
    "https://www.youtube.com/watch?v=qQfuo06M7Ec&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=148",
    "https://www.youtube.com/watch?v=Jn01ZkZa3Xs&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=149",
    "https://www.youtube.com/watch?v=Evf2DLCbF9Y&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=150",
    "https://www.youtube.com/watch?v=n8ShH0LTYoA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=151",
    "https://www.youtube.com/watch?v=YZ69pdSsrkc&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=152",
    "https://www.youtube.com/watch?v=0qX8Rj0lvpk&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=153",
    "https://www.youtube.com/watch?v=TQ8abXJMGtY&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=154",
    "https://www.youtube.com/watch?v=Bz4jmqzOE9s&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=155",
    "https://www.youtube.com/watch?v=AHTe92Rggyc&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=156",
    "https://www.youtube.com/watch?v=ZaXzr2KdRes&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=157",
    "https://www.youtube.com/watch?v=oiON7nAGIwo&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=158",
    "https://www.youtube.com/watch?v=KEaibOWBk58&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=159",
    "https://www.youtube.com/watch?v=QY6Oqli1LmI&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=160",
    "https://www.youtube.com/watch?v=iyzyb_-qcWI&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=161",
    "https://www.youtube.com/watch?v=1ziaEdknbQc&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=162",
    "https://www.youtube.com/watch?v=ioTH9DE_XUY&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=163",
    "https://www.youtube.com/watch?v=QNJUdGC5Ijc&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=164",
    "https://www.youtube.com/watch?v=NgOdy7-cED4&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=165",
    "https://www.youtube.com/watch?v=RFFcM3P1iJ0&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=166",
    "https://www.youtube.com/watch?v=JflLLJX4d1Y&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=167",
    "https://www.youtube.com/watch?v=2CVgGhZeSq4&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=168",
    "https://www.youtube.com/watch?v=wZqNuuMO3i0&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=169",
    "https://www.youtube.com/watch?v=DJsnRnUlOwI&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=170",
    "https://www.youtube.com/watch?v=EtUoBG6gM-Y&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=171",
    "https://www.youtube.com/watch?v=JDDNUTNCbus&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=172",
    "https://www.youtube.com/watch?v=NGXIX4KMhyo&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=173",
    "https://www.youtube.com/watch?v=0FxiqJyPi40&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=174",
    "https://www.youtube.com/watch?v=yUHhOcMOnAA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=175",
    "https://www.youtube.com/watch?v=HNre3AAFxys&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=176",
    "https://www.youtube.com/watch?v=VGS0qv4B124&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=177",
    "https://www.youtube.com/watch?v=YYj9ICGk3fQ&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=178",
    "https://www.youtube.com/watch?v=2bDcCFU5AmY&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=179",
    "https://www.youtube.com/watch?v=YEzd3ClxWgQ&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=180",
    "https://www.youtube.com/watch?v=DoKGfd1q3kA&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=181",
    "https://www.youtube.com/watch?v=3G5J01ajZTs&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=182",
    "https://www.youtube.com/watch?v=qYfcJP3EXoU&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=183",
    "https://www.youtube.com/watch?v=8_ExsCzbeSw&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=184",
    "https://www.youtube.com/watch?v=ZC27k_jlMrY&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=185",
    "https://www.youtube.com/watch?v=rPWwItgnnHw&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=186",
    "https://www.youtube.com/watch?v=vDZcIr0s-do&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=187",
    "https://www.youtube.com/watch?v=gLXFdydaS3g&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=188",
    "https://www.youtube.com/watch?v=Kif4pohYNGw&list=PLS0pq2M-6hSKrNXAl0lkZKQRmKNR2oqwJ&index=189"
]
    # Automatically extract IDs from the URLs
    video_ids = [extract_video_id(url) for url in video_urls]
    
    print("Initializing YouTube transcript fetching pipeline...")
    
    manager = YouTubeTranscriptManager(output_dir="data_pipeline/output")
    raw_transcripts, fetch_stats = manager.process_videos(video_ids)
    
    print("Initializing chunking pipeline...")
    chunker = TranscriptChunker(min_chunk_duration=30.0, pause_threshold=1.0)
    
    for video_id, raw_data in raw_transcripts.items():
        output_path = f"data_pipeline/output/{video_id}.json"
        
        chunked_data = chunker.process(raw_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunked_data, f, indent=4, ensure_ascii=False)
        print(f"Saved directly chunked transcript for {video_id} to {output_path}")

    # Calculate total existing JSON files in output directory
    total_existing = 0
    if os.path.exists("data_pipeline/output"):
        total_existing = len([f for f in os.listdir("data_pipeline/output") if f.endswith('.json')])
    
    print("\n" + "="*50)
    print("🎬 PIPELINE EXECUTION SUMMARY")
    print("="*50)
    print(f"Total Video URLs Given:           {fetch_stats['total_given']}")
    print(f"Total successfully processed:     {fetch_stats['success']}")
    print(f"Total existing in output/ dir:    {total_existing}")
    print("\n[ SKIPPED VIDEOS ]")
    print(f"Skipped (Already Processed):      {fetch_stats['skipped_already_exists']}")
    print(f"Skipped (Uploaded Before 2022):   {fetch_stats['skipped_pre2022']}")
    print("\n[ ERRORS CATEGORIZED ]")
    print(f"No Transcript Found / Disabled:   {fetch_stats['error_transcript_not_found']}")
    print(f"Transcript Exists (No Marathi):   {fetch_stats['error_no_native_marathi']}")
    print(f"Other Unknown Errors:             {fetch_stats['error_other']}")
    print("="*50)
    print("\nPipeline execution finished. Check output/ directory and ingestion.log")
