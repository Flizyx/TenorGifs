import os
import json
import requests
import random
from PIL import Image, ImageSequence

# 📌 CONFIGURATION
tenor_api_key = "YOUR_API_KEY"
if not tenor_api_key:
    raise ValueError("TENOR_API_KEY is not defined in environment variables.")

output_dir = "TenorGifs/output"
os.makedirs(output_dir, exist_ok=True)
target_resolution = (320, 240)  # Fixed resolution

def get_gif_url(query):
    pos = random.randint(0, 20)  # Adds variety to the search
    url = f"https://tenor.googleapis.com/v2/search?q={query}&key={tenor_api_key}&client_key=my_test_app&limit=10&contentfilter=high&pos={pos}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        results = [gif["media_formats"]["gif"]["url"] for gif in data.get("results", [])]
        return random.choice(results) if results else None
    return None

def download_gif(url, filename):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return filename
    return None

def trim_gif(gif_path, max_duration=2000):
    img = Image.open(gif_path)
    frames = []
    durations = []
    total_duration = 0
    for frame in ImageSequence.Iterator(img):
        d = frame.info.get("duration", 100)
        if total_duration + d > max_duration:
            break
        frames.append(frame.copy())
        durations.append(d)
        total_duration += d
    if total_duration < sum(frame.info.get("duration", 100) for frame in ImageSequence.Iterator(img)):
        output_path = gif_path.replace(".gif", "_trimmed.gif")
        frames[0].save(output_path, save_all=True, append_images=frames[1:], loop=0, duration=durations)
        os.remove(gif_path)
        return output_path
    return gif_path

def resize_frame_with_letterbox(frame, target_size):
    target_w, target_h = target_size
    frame = frame.convert("RGB")
    orig_w, orig_h = frame.size
    scale = min(target_w / orig_w, target_h / orig_h)
    new_w = int(orig_w * scale)
    new_h = int(orig_h * scale)
    resized_frame = frame.resize((new_w, new_h), Image.LANCZOS)
    new_frame = Image.new("RGB", (target_w, target_h), (0, 0, 0))
    paste_x = (target_w - new_w) // 2
    paste_y = (target_h - new_h) // 2
    new_frame.paste(resized_frame, (paste_x, paste_y))
    return new_frame

def merge_gifs(gif_paths):
    all_frames = []
    all_durations = []
    for path in gif_paths:
        img = Image.open(path)
        for frame in ImageSequence.Iterator(img):
            all_frames.append(frame.copy())
            all_durations.append(frame.info.get("duration", 100))
    return all_frames, all_durations

def adjust_final_gif_duration(frames, durations, max_total=4000):
    total_duration = sum(durations)
    if total_duration > max_total and frames:
        num_frames = len(frames)
        new_duration = max(10, int(max_total / num_frames))
        return [new_duration] * num_frames
    return durations

def process_transcription(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        transcriptions = json.load(file)
    
    for idx, entry in enumerate(transcriptions):
        query = " ".join(entry["words"])
        temp_gif_paths = []
        for _ in range(3):  # Get 3 GIFs for variety
            gif_url = get_gif_url(query)
            if gif_url:
                gif_filename = os.path.join(output_dir, f"{entry['timestamp']}_{random.randint(1000,9999)}.gif")
                download_gif(gif_url, gif_filename)
                temp_gif_paths.append(trim_gif(gif_filename))
        if temp_gif_paths:
            frames, durations = merge_gifs(temp_gif_paths)
            frames = [resize_frame_with_letterbox(frame, target_resolution) for frame in frames]
            new_durations = adjust_final_gif_duration(frames, durations, max_total=4000)
            output_path = os.path.join(output_dir, f"final_{idx}.gif")
            frames[0].save(output_path, save_all=True, append_images=frames[1:], loop=0, duration=new_durations)
            # Delete temporary GIFs
            for path in temp_gif_paths:
                if os.path.exists(path):
                    os.remove(path)
            print(f"✅ GIF generated: {output_path}")
    print("🚀 All GIFs have been successfully generated!")

# Ensure the transcription file exists in the specified path
transcription_file = "TenorGifs/transcriptions.json"
if os.path.exists(transcription_file):
    process_transcription(transcription_file)
else:
    print(f"⚠️ Transcription file not found: {transcription_file}")
