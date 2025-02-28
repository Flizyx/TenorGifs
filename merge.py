import os
from PIL import Image, ImageSequence

# 📌 CONFIGURATION
input_gifs = ["TenorGifs/images/soe-salome.gif", "TenorGifs/images/wasted-angry.gif", "TenorGifs/images/lets-go-lets-do-it.gif"]
output_gif = "TenorGifs/images/merged_output.gif"
target_resolution = (320, 240)  # Fixed size
max_total_duration = 4000  # Max total duration in ms

def resize_frame_with_letterbox(frame, target_size):
    target_w, target_h = target_size
    frame = frame.convert("RGBA")  # Preserve transparency
    orig_w, orig_h = frame.size
    scale = min(target_w / orig_w, target_h / orig_h)
    new_w, new_h = int(orig_w * scale), int(orig_h * scale)
    resized_frame = frame.resize((new_w, new_h), Image.LANCZOS)

    # Center the resized frame with black padding
    new_frame = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    paste_x, paste_y = (target_w - new_w) // 2, (target_h - new_h) // 2
    new_frame.paste(resized_frame, (paste_x, paste_y), resized_frame)
    
    return new_frame

def merge_gifs(gif_paths, output_path, target_size, max_duration):
    all_frames = []
    all_durations = []

    for path in gif_paths:
        if not os.path.exists(path):
            print(f"⚠️ File not found: {path}")
            continue

        img = Image.open(path)
        for frame in ImageSequence.Iterator(img):
            all_frames.append(resize_frame_with_letterbox(frame.copy(), target_size))
            all_durations.append(frame.info.get("duration", 100))

    if not all_frames:
        print("❌ No valid GIFs found. Exiting.")
        return

    # Normalize duration if exceeding max duration
    total_duration = sum(all_durations)
    if total_duration > max_duration:
        frame_count = len(all_frames)
        new_duration = max(10, max_duration // frame_count)
        all_durations = [new_duration] * frame_count

    # Save the final merged GIF
    all_frames[0].save(output_path, save_all=True, append_images=all_frames[1:], loop=0, duration=all_durations)
    print(f"✅ Merged GIF saved: {output_path}")

merge_gifs(input_gifs, output_gif, target_resolution, max_total_duration)
