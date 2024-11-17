import librosa
import numpy as np

def intensity_calculation(y):
    reference_spl = 94
    rms = librosa.feature.rms(y=y)
    intensity = librosa.amplitude_to_db(rms, ref=np.max).mean()
    intensity += reference_spl
    return round(intensity, 2)

def pitch_calculation(y):
    f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
    f0_clean_mean = f0[~np.isnan(f0)].mean()
    return round(f0_clean_mean, 2)

def pause_per_minute_calculation(y, sr, audio_duration_minutes):
    rms = librosa.feature.rms(y=y).flatten()
    frames = range(len(rms))
    times = librosa.frames_to_time(frames, sr=sr)
    energy_threshold = np.percentile(rms, 5)
    low_energy_frames = rms < energy_threshold
    pauses = []
    start = None

    for i, is_low in enumerate(low_energy_frames):
        if is_low and start is None and times[i] > 0.2:
            start = times[i]
        elif not is_low and start is not None and times[i] < audio_duration_minutes * 60 - 0.2:
            end = times[i]
            duration = end - start
            pauses.append((start, end, duration))
            start = None

    short_pauses = [pause for pause in pauses if pause[2] < 0.2]
    medium_pauses = [pause for pause in pauses if 0.2 <= pause[2] < 1]
    long_pauses = [pause for pause in pauses if pause[2] >= 1]

    return {
        "short_pauses_per_minute": round(len(short_pauses) / audio_duration_minutes),
        "medium_pauses_per_minute": round(len(medium_pauses) / audio_duration_minutes),
        "long_pauses_per_minute": round(len(long_pauses) / audio_duration_minutes)
    }