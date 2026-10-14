#!/usr/bin/env python3
"""
ClimateWise - Automated 1080p Video Pitch Generator
Creates high-definition cinematic visual slides with Pillow,
synthesizes voiceover narration using macOS TTS,
and compiles the final MP4 presentation video via ffmpeg.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1920
HEIGHT = 1080
FPS = 30

FONT_TITLE_PATH = "/System/Library/Fonts/HelveticaNeue.ttc"
FONT_MONO_PATH = "/System/Library/Fonts/Menlo.ttc"


def get_font(path: str, size: int, index: int = 0):
    try:
        return ImageFont.truetype(path, size, index=index)
    except Exception:
        try:
            return ImageFont.load_default()
        except Exception:
            return None


font_brand = get_font(FONT_TITLE_PATH, 42, 1) or ImageFont.load_default()
font_h1 = get_font(FONT_TITLE_PATH, 68, 1) or ImageFont.load_default()
font_h2 = get_font(FONT_TITLE_PATH, 36, 0) or ImageFont.load_default()
font_body = get_font(FONT_TITLE_PATH, 30, 0) or ImageFont.load_default()
font_mono = get_font(FONT_MONO_PATH, 24, 0) or ImageFont.load_default()
font_metric_val = get_font(FONT_TITLE_PATH, 54, 1) or ImageFont.load_default()
font_metric_lbl = get_font(FONT_TITLE_PATH, 20, 0) or ImageFont.load_default()
font_subtitle = get_font(FONT_TITLE_PATH, 26, 0) or ImageFont.load_default()


def create_base_canvas():
    """Generates an aesthetic deep cyber-gradient canvas (1920x1080)."""
    img = Image.new("RGBA", (WIDTH, HEIGHT), (6, 11, 20, 255))
    draw = ImageDraw.Draw(img)

    # Gradient background: Dark navy (#060B14) to deep teal-emerald (#081C1B)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(6 + ratio * 8)
        g = int(11 + ratio * 24)
        b = int(20 + ratio * 15)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

    # Top Navigation Glass Bar
    draw.rectangle([(0, 0), (WIDTH, 90)], fill=(12, 22, 38, 220))
    draw.line([(0, 90), (WIDTH, 90)], fill=(34, 197, 94, 90), width=2)

    # Branding
    draw.text((80, 24), "CLIMATEWISE", font=font_brand, fill=(34, 197, 94, 255))
    draw.text((360, 34), "| Autonomous Climate Risk Protocol", font=font_h2, fill=(148, 163, 184, 255))

    # Badges on Top Right
    badges = [
        ("NVIDIA PARTNER", (16, 185, 129)),
        ("BASE L2 (COINBASE)", (59, 130, 246)),
        ("AKASH DePIN", (168, 85, 247)),
    ]
    cur_x = WIDTH - 80
    for label, color in reversed(badges):
        bbox = draw.textbbox((0, 0), label, font=font_mono)
        w = bbox[2] - bbox[0] + 28
        cur_x -= w
        draw.rounded_rectangle([(cur_x, 26), (cur_x + w, 66)], radius=12, fill=(color[0], color[1], color[2], 30), outline=(color[0], color[1], color[2], 180), width=1)
        draw.text((cur_x + 14, 33), label, font=font_mono, fill=(color[0], color[1], color[2], 255))
        cur_x -= 16

    # Bottom Subtitle Bar
    draw.rectangle([(0, HEIGHT - 80), (WIDTH, HEIGHT)], fill=(10, 16, 28, 240))
    draw.line([(0, HEIGHT - 80), (WIDTH, HEIGHT - 80)], fill=(45, 55, 72, 180), width=1)

    return img, draw


SCENES = [
    {
        "id": 1,
        "title": "Planetary Non-Stationarity",
        "subtitle": "The $1.8 Trillion Uninsured Climate Protection Gap",
        "badge": "THE MACRO CRISIS",
        "metrics": [
            ("$1.8T", "Global Protection Void", (239, 68, 68)),
            ("45+ Days", "Legacy Claims Delay", (245, 158, 11)),
            ("82%", "Uninsured Cropland (Brazil)", (239, 68, 68)),
            ("42%", "Wasted SG&A Overhead", (245, 158, 11)),
        ],
        "bullets": [
            "Climate volatility is accelerating at non-linear, power-law speed.",
            "Historical Gaussian actuarial tables are mathematically broken.",
            "Traditional global reinsurers (Swiss Re, Munich Re) are pulling out.",
            "A single catastrophic drought or flood destroys entire agricultural regions.",
        ],
        "voice": "Climate volatility is accelerating at non-linear speed. Yet the seven-trillion-dollar global insurance industry remains trapped in a 300-year-old analog paradigm: manual loss adjusters, forty-five-day claim delays, and a staggering 1.8 trillion dollar protection gap."
    },
    {
        "id": 2,
        "title": "Meet ClimateWise",
        "subtitle": "The World's First Autonomous Climate Risk Clearinghouse",
        "badge": "THE SOLUTION",
        "metrics": [
            ("< 2.4s", "Instant Smart Settlement", (34, 197, 94)),
            ("$0.003", "Base L2 Gas Fee", (59, 130, 246)),
            ("100%", "Parametric & Algorithmic", (168, 85, 247)),
            ("0", "Paper Adjusters or Litigation", (34, 197, 94)),
        ],
        "bullets": [
            "Replaces analog bureaucracy with high-resolution satellite remote sensing.",
            "Actuarial neural networks predict loss distributions in milliseconds.",
            "Programmatic on-chain policy tokenization (ERC-3525 Semi-Fungible Tokens).",
            "Zero claims paperwork: instant payout when physical thresholds trigger.",
        ],
        "voice": "Meet ClimateWise. The world's first autonomous climate risk clearinghouse. Powered by NVIDIA supercomputing and decentralized AI, ClimateWise replaces paper bureaucracy with satellite remote sensing, deep neural actuarial pricing, and programmatic on-chain execution."
    },
    {
        "id": 3,
        "title": "NVIDIA Partner Advantage & Triangulated Oracles",
        "subtitle": "Byzantine Fault Tolerant Truth Engine with Cryptographic Proofs",
        "badge": "ENTERPRISE MOAT",
        "metrics": [
            ("14ms", "TensorRT Model Latency", (16, 185, 129)),
            ("2-of-3", "Consensus Triangulation", (168, 85, 247)),
            ("800+", "INMET Ground Stations", (59, 130, 246)),
            ("SHA-256", "Canonical Proof of Loss", (245, 158, 11)),
        ],
        "bullets": [
            "Official NVIDIA Partner: Leveraging Earth-2 supercomputing & TensorRT.",
            "Akash DePIN GPU Cluster: 74% compute cost reduction vs AWS/GCP.",
            "Truth Triangulation: Sentinel-2 Satellite + Ground Sensors + Radar.",
            "Deterministic audit dossier: Hash recorded on BaseScan on every payout.",
        ],
        "voice": "As an official NVIDIA Partner, our spatial-temporal neural networks simulate microclimate loss distributions in milliseconds. No payout relies on a single feed: our Byzantine-tolerant oracle triangulates orbital satellites, in-situ ground sensors, and civil radar data into tamper-proof cryptographic proofs."
    },
    {
        "id": 4,
        "title": "Live On-Chain Settlement on Base (Coinbase L2)",
        "subtitle": "Contract 0x01dD68040B926Fd4938cD43Ae3c88758874DD0D0 Verified on BaseScan",
        "badge": "PROVEN ON-CHAIN EXECUTION",
        "metrics": [
            ("R$ 108.150", "Token #1 Live Coverage", (34, 197, 94)),
            ("50%", "Oracle Payout Executed", (59, 130, 246)),
            ("Block #48M", "Base Sepolia L2", (168, 85, 247)),
            ("100%", "Test Suite Green (13/13)", (34, 197, 94)),
        ],
        "bullets": [
            "Smart Contract ClimatePolicy.sol deployed and verified on BaseScan.",
            "Real policy minted on-chain: Token ID #1 (R$ 108.150,69 collateral).",
            "Real payout executed via triggerPayoutWithProof() in block #48091393.",
            "Coinbase ecosystem alignment: Native USDC liquidity and Smart Wallets.",
        ],
        "voice": "Deployed on Coinbase's Base Layer-2, policies are minted as semi-fungible ERC-3525 tokens. When severe drought strikes, parametric smart contracts trigger immediate payouts directly to farmers in under 2.4 seconds, with a fraction of a cent in gas fees."
    },
    {
        "id": 5,
        "title": "Agribusiness TAM & Institutional RWA Tokenomics",
        "subtitle": "Uncorrelated 12-18% CatBond Yields & Deflationary Buyback-and-Burn",
        "badge": "MARKET SCALE & ECONOMICS",
        "metrics": [
            ("$540B", "Brazil Agribusiness Output", (34, 197, 94)),
            ("14-18%", "Institutional CatBond APY", (168, 85, 247)),
            ("2.5%", "Protocol Take-Rate", (59, 130, 246)),
            ("50%", "Take-Rate Buyback & Burn", (245, 158, 11)),
        ],
        "bullets": [
            "Brazil First: #1 global exporter of Soy, Corn, Coffee, Sugar, and Beef.",
            "Over R$ 1.5B annual federal premium subsidies seeking digital platforms.",
            "Institutional CatBond Vaults: Zero beta to S&P 500, NASDAQ, or Crypto.",
            "High-margin software model: Negative working capital and 70%+ EBITDA.",
        ],
        "voice": "Starting in Brazil—the world's agricultural breadbasket where 82% of crops lack private coverage—ClimateWise unlocks the 140 billion dollar parametric market. Our institutional CatBond vaults channel uncorrelated double-digit yield to global capital, while 50% of protocol fees drive programmatic buyback and burn of the CW token."
    },
    {
        "id": 6,
        "title": "The Investment Opportunity: Series Seed / A",
        "subtitle": "Raising $8.5M USD to Scale to $100M+ in Tokenized Gross Written Premium",
        "badge": "SERIES SEED / A ROUND",
        "metrics": [
            ("$8.5M", "Target Raise (SAFE+Warrant)", (34, 197, 94)),
            ("$100M", "18-Month GWP Target", (59, 130, 246)),
            ("1.5M", "Hectares Protected", (168, 85, 247)),
            ("a16z/Sequoia", "Target Tier-1 Leads", (245, 158, 11)),
        ],
        "bullets": [
            "Use of Funds: 40% AI Supercomputing, 25% Reinsurance Vaults, 20% GTM.",
            "Live Proof-of-Work: Active Akash DePIN cluster, verified Base L2 contract.",
            "Strategic Alliance: NVIDIA Partner Network, Base Developer Ecosystem.",
            "Join us: The future of planetary resilience is autonomous.",
        ],
        "voice": "ClimateWise is already live on-chain, verified on BaseScan, and operational on DePIN GPU clusters. We are raising an 8.5 million dollar Seed round to scale to one hundred million dollars in underwritten premiums. The future of planetary resilience is autonomous. Join us at ClimateWise."
    }
]


def render_scene_slide(scene: dict) -> Image.Image:
    """Renders a single high-definition 1080p slide with cards and typography."""
    img, draw = create_base_canvas()

    # Category Badge
    badge_text = scene["badge"]
    draw.rounded_rectangle([(80, 120), (380, 160)], radius=10, fill=(34, 197, 94, 25), outline=(34, 197, 94, 160), width=1)
    draw.text((98, 128), badge_text, font=font_mono, fill=(34, 197, 94, 255))

    # Main Headline & Subheadline
    draw.text((80, 175), scene["title"], font=font_h1, fill=(248, 250, 252, 255))
    draw.text((80, 260), scene["subtitle"], font=font_h2, fill=(148, 163, 184, 255))

    # Horizontal Divider Line
    draw.line([(80, 315), (WIDTH - 80, 315)], fill=(45, 55, 72, 120), width=1)

    # 4 Metric Cards Across
    metrics = scene["metrics"]
    card_w = 405
    card_gap = 30
    for idx, (val, lbl, col) in enumerate(metrics):
        cx = 80 + idx * (card_w + card_gap)
        cy = 345
        draw.rounded_rectangle([(cx, cy), (cx + card_w, cy + 155)], radius=18, fill=(15, 25, 42, 210), outline=(col[0], col[1], col[2], 120), width=1)
        draw.text((cx + 28, cy + 24), val, font=font_metric_val, fill=(col[0], col[1], col[2], 255))
        draw.text((cx + 28, cy + 96), lbl, font=font_metric_lbl, fill=(203, 213, 225, 255))

    # Detailed Content Card (Left)
    draw.rounded_rectangle([(80, 535), (WIDTH - 80, 890)], radius=24, fill=(13, 22, 38, 210), outline=(51, 65, 85, 150), width=1)

    # Header in detailed card
    draw.text((120, 565), "KEY ARCHITECTURAL PILLARS & VALUE PROPOSITION", font=font_mono, fill=(34, 197, 94, 255))

    # Bullets
    bullets = scene["bullets"]
    for b_idx, bullet in enumerate(bullets):
        by = 620 + b_idx * 60
        # Cyan glowing bullet pip
        draw.ellipse([(120, by + 8), (134, by + 22)], fill=(56, 189, 248, 255))
        draw.text((155, by), bullet, font=font_body, fill=(241, 245, 249, 255))

    # Subtitle ticker on bottom bar
    subtitle_text = f"NARRATION: \"{scene['voice'][:115]}...\""
    draw.text((80, HEIGHT - 56), subtitle_text, font=font_subtitle, fill=(203, 213, 225, 255))

    return img


def generate_all_video():
    output_dir = Path("docs")
    output_dir.mkdir(parents=True, exist_ok=True)
    client_public = Path("client/public")
    client_public.mkdir(parents=True, exist_ok=True)

    master_mp4 = output_dir / "climatewise_presentation_video.mp4"
    public_mp4 = client_public / "climatewise_presentation_video.mp4"

    temp_dir = tempfile.mkdtemp(prefix="cw_video_")
    print(f"Working in temp directory: {temp_dir}")

    scene_clips = []

    for scene in SCENES:
        s_id = scene["id"]
        print(f"\n[Scene {s_id}/6] Processing '{scene['title']}'...")

        # 1. Render PNG slide
        slide_img = render_scene_slide(scene)
        png_path = os.path.join(temp_dir, f"slide_{s_id}.png")
        slide_img.save(png_path)

        # 2. Synthesize audio with macOS say
        aiff_path = os.path.join(temp_dir, f"audio_{s_id}.aiff")
        wav_path = os.path.join(temp_dir, f"audio_{s_id}.wav")

        subprocess.run(["say", "-v", "Samantha", "-r", "165", "-o", aiff_path, scene["voice"]], check=True)
        # Convert to standard 44.1kHz stereo wav
        subprocess.run(["ffmpeg", "-y", "-i", aiff_path, "-ar", "44100", "-ac", "2", wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 3. Get audio duration
        duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", wav_path]
        duration_str = subprocess.check_output(duration_cmd).decode().strip()
        duration = float(duration_str) + 0.8  # Add 0.8s tail padding for natural pacing
        print(f"  Audio duration: {duration:.2f}s")

        # 4. Generate scene MP4 with subtle Ken Burns zoom/pan
        clip_path = os.path.join(temp_dir, f"scene_{s_id}.mp4")
        ffmpeg_clip_cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", png_path,
            "-i", wav_path,
            "-vf", f"scale=1920:1080,zoompan=z='min(zoom+0.0003,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(duration*FPS)}:s=1920x1080",
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            clip_path
        ]
        subprocess.run(ffmpeg_clip_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        scene_clips.append(clip_path)
        print(f"  Scene {s_id} clip rendered successfully.")

    # 5. Concatenate all scenes into master video
    concat_list_path = os.path.join(temp_dir, "concat.txt")
    with open(concat_list_path, "w") as f:
        for clip in scene_clips:
            f.write(f"file '{clip}'\n")

    print(f"\n[Final Assembly] Stitching all 6 scenes into master presentation video...")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(master_mp4)
    ]
    subprocess.run(concat_cmd, check=True)

    # Copy to client/public for immediate in-app viewing
    subprocess.run(["cp", str(master_mp4), str(public_mp4)], check=True)

    print("\n==================================================================")
    print(f"SUCCESS! Presentation Video Generated!")
    print(f"Master Video Path: {master_mp4}")
    print(f"Public App Path:   {public_mp4}")
    print("==================================================================")


if __name__ == "__main__":
    generate_all_video()
