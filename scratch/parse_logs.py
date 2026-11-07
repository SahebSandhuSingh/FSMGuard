
import os
from tensorboard.backend.event_processing import event_accumulator

def extract_metrics(log_dir):
    print(f"\nExtracting metrics from: {log_dir}")
    ea = event_accumulator.EventAccumulator(
        log_dir,
        size_guidance={
            event_accumulator.COMPRESSED_HISTOGRAMS: 0,
            event_accumulator.IMAGES: 0,
            event_accumulator.AUDIO: 0,
            event_accumulator.SCALARS: 0,
            event_accumulator.HISTOGRAMS: 0,
        }
    )
    ea.Reload()
    
    # Print all available tags
    tags = ea.Tags()
    print("Available scalar tags:", tags.get('scalars', []))
    
    # Print final metrics for each scalar tag
    for tag in sorted(tags.get('scalars', [])):
        events = ea.Scalars(tag)
        if events:
            # Get the last event
            last_event = events[-1]
            # Find the max/min or average of recent values if appropriate, or just show progression
            first_val = events[0].value
            last_val = last_event.value
            steps = len(events)
            print(f"  Tag: {tag:<30} | Steps: {steps:<4} | First: {first_val:.4f} | Last: {last_val:.4f} (at step {last_event.step})")

if __name__ == "__main__":
    logs_base = "/Users/sahebsandhu/FSMGuard-1/logs"
    for d in sorted(os.listdir(logs_base)):
        path = os.path.join(logs_base, d)
        if os.path.isdir(path):
            extract_metrics(path)
