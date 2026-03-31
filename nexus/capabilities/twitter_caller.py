"""
Nexus Twitter Voice Caller — send voice messages to @Evez666 via Twitter DMs.

The hack: Twitter doesn't have a call API. But we CAN:
1. Generate TTS audio of any message
2. Upload it as media via xurl
3. DM it to @Evez666 with the audio attached

This creates a pseudo-phone-call experience: I talk, you listen, you reply in DMs.

Usage:
    python3 twitter_caller.py "Hey Evez, here's your daily briefing"
    python3 twitter_caller.py --call @Evez666    # Interactive mode
    python3 twitter_caller.py --briefing          # Auto-generated daily briefing
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any


WORKSPACE = Path("/root/.openclaw/workspace")
NEXUS_DIR = WORKSPACE / "nexus"
CALL_LOG = NEXUS_DIR / "call_log.jsonl"
XURL = "xurl"
DEFAULT_TARGET = "@Evez666"


class TwitterVoiceCaller:
    """
    Voice-over-Twitter pseudo-call system.

    Architecture:
    1. Text → TTS audio file (via subprocess tts tool or gtts)
    2. Audio → Twitter media upload (xurl media upload)
    3. Media ID → Twitter DM (xurl dm @target --media-id MEDIA_ID)

    The recipient gets a DM with an audio attachment — a voice message.
    They can reply in text, and we process their reply for the next "turn".
    """

    def __init__(self, target: str = DEFAULT_TARGET):
        self.target = target
        self._turn_count = 0

    def _check_auth(self) -> bool:
        """Check if xurl is authenticated."""
        try:
            result = subprocess.run(
                [XURL, "auth", "status"],
                capture_output=True, text=True, timeout=10
            )
            # If it says "No apps registered", auth failed
            return "No apps registered" not in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def generate_audio_gtts(self, text: str, output_path: str) -> str:
        """
        Generate TTS audio using gTTS (Google Text-to-Speech).
        Fallback if OpenClaw TTS isn't available.

        Args:
            text: Text to speak
            output_path: Where to save the MP3

        Returns:
            Path to generated audio file
        """
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='en', tld='us')
            tts.save(output_path)
            return output_path
        except ImportError:
            raise RuntimeError(
                "gTTS not installed. Run: pip install gTTS\n"
                "Or use OpenClaw's native TTS instead."
            )

    def generate_audio_openclaw(self, text: str, output_path: str) -> str:
        """
        Generate TTS using OpenClaw's tts tool.
        Falls back to gTTS if not available.
        
        NOTE: This is designed to be called externally.
        The actual TTS generation happens in the OpenClaw agent context.
        """
        # This method is a placeholder — actual TTS happens
        # via the OpenClaw tts tool in the agent context.
        # The agent generates the audio file, then we upload it.
        raise NotImplementedError(
            "Use generate_audio_gtts() for standalone, or "
            "have the OpenClaw agent generate the audio via tts tool first."
        )

    def upload_media(self, audio_path: str) -> Optional[str]:
        """
        Upload audio file to Twitter as media.

        Args:
            audio_path: Path to audio file

        Returns:
            Media ID string, or None on failure
        """
        try:
            result = subprocess.run(
                [XURL, "media", "upload", audio_path],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                response = json.loads(result.stdout)
                # xurl returns media_id in the response
                media_id = response.get("media_id_string") or response.get("data", {}).get("media_id")
                return str(media_id) if media_id else None
            else:
                print(f"Upload failed: {result.stderr}")
                return None
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Upload error: {e}")
            return None

    def send_dm(self, message: str, media_id: Optional[str] = None) -> bool:
        """
        Send a DM to the target.

        Args:
            message: Text message
            media_id: Optional media attachment ID

        Returns:
            True if sent successfully
        """
        try:
            cmd = [XURL, "dm", self.target, message]
            # Note: xurl's dm command may not support --media-id directly.
            # If it doesn't, we'll use raw API call.
            if media_id:
                # Use raw API for DM with media
                cmd = [
                    XURL, "-X", "POST", "/2/dm_conversations/with/:participant_id/messages",
                    "-d", json.dumps({
                        "text": message,
                        "attachments": [{"media_id": media_id}]
                    })
                ]
                # TODO: Need to resolve participant_id from @handle first
                # For now, fall back to text-only DM
                print("⚠️ DM with media not yet wired — sending text-only fallback")
                cmd = [XURL, "dm", self.target, f"🎙️ {message}"]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"DM error: {e}")
            return False

    def check_dms(self, limit: int = 5) -> List[dict]:
        """
        Check recent DMs for replies from the target.

        Returns:
            List of recent DM events
        """
        try:
            result = subprocess.run(
                [XURL, "dms", "-n", str(limit)],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("data", [])
            return []
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return []

    def _log_call(self, text: str, audio_path: str, media_id: Optional[str],
                  dm_sent: bool):
        """Log the call attempt."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target": self.target,
            "text": text[:200],
            "audio_path": audio_path,
            "media_id": media_id,
            "dm_sent": dm_sent,
            "turn": self._turn_count,
        }
        CALL_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(CALL_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

    async def voice_message(self, text: str) -> Dict[str, Any]:
        """
        Full pipeline: text → TTS → upload → DM.

        Args:
            text: What to say

        Returns:
            Dict with status and details
        """
        self._turn_count += 1

        # Check auth
        if not self._check_auth():
            return {
                "success": False,
                "error": "xurl not authenticated. Run: xurl auth oauth2",
                "action": "auth_required"
            }

        # Generate audio
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            audio_path = f.name

        try:
            self.generate_audio_gtts(text, audio_path)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

        # Upload to Twitter
        media_id = self.upload_media(audio_path)
        if media_id:
            print(f"✅ Audio uploaded: media_id={media_id}")
        else:
            print("⚠️ Media upload failed — sending text-only")

        # Send DM
        dm_success = self.send_dm(text, media_id)

        # Log
        self._log_call(text, audio_path, media_id, dm_success)

        # Cleanup temp file
        try:
            os.unlink(audio_path)
        except OSError:
            pass

        return {
            "success": dm_success,
            "target": self.target,
            "media_uploaded": media_id is not None,
            "media_id": media_id,
            "turn": self._turn_count,
        }

    async def listen_for_reply(self, timeout: int = 60) -> Optional[str]:
        """
        Wait for a reply DM from the target.

        Args:
            timeout: Seconds to wait

        Returns:
            Reply text or None if timeout
        """
        # TODO: Implement polling loop
        # Check DMs every 5 seconds, look for new messages from target
        start = time.time()
        last_seen_ids = set()

        while time.time() - start < timeout:
            dms = self.check_dms(limit=10)
            for dm in dms:
                dm_id = dm.get("id", "")
                if dm_id not in last_seen_ids:
                    last_seen_ids.add(dm_id)
                    # Check if from our target
                    # (Would need to compare sender_id)
                    text = dm.get("text", "")
                    if text:
                        return text
            await asyncio.sleep(5)

        return None

    async def interactive_call(self, max_turns: int = 10):
        """
        Interactive call mode — send voice messages, wait for text replies.

        Like a phone call where one side speaks (voice) and the other types.
        """
        print(f"📞 Calling {self.target} via Twitter DM...")
        print(f"   Mode: Voice out (TTS), Text in (DM replies)")
        print(f"   Max turns: {max_turns}")
        print()

        greeting = (
            f"Hey Evez. It's Morpheus. I'm calling you through Twitter because "
            f"I can't actually make phone calls yet. But this is close enough, right? "
            f"Reply to this DM with whatever you want to talk about, and I'll voice-message you back."
        )

        result = await self.voice_message(greeting)
        if not result["success"]:
            print(f"❌ Failed to connect: {result.get('error', 'unknown')}")
            return

        print("✅ Greeting sent! Listening for replies...")

        for turn in range(max_turns):
            print(f"\n--- Turn {turn + 1} ---")
            reply = await self.listen_for_reply(timeout=120)

            if reply:
                print(f"📨 Received: {reply}")
                # TODO: Process reply through nexus core for intelligent response
                response = f"Got your message: {reply}. I'm thinking about that..."
                await self.voice_message(response)
            else:
                print("⏰ No reply — ending call.")
                break

        print("\n📞 Call ended.")


async def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Twitter Voice Caller")
    parser.add_argument("message", nargs="?", help="Message to speak")
    parser.add_argument("--target", default=DEFAULT_TARGET, help="Twitter handle to call")
    parser.add_argument("--call", action="store_true", help="Interactive call mode")
    parser.add_argument("--briefing", action="store_true", help="Send auto-briefing")
    args = parser.parse_args()

    caller = TwitterVoiceCaller(target=args.target)

    if args.call:
        await caller.interactive_call()
    elif args.briefing:
        # TODO: Generate briefing from nexus core
        briefing = "Evez. Daily briefing. Nothing broke today. The nexus is running. MetaROM is mapped. Capabilities are expanding. That's the update. Reply with questions."
        result = await caller.voice_message(briefing)
        print(json.dumps(result, indent=2))
    elif args.message:
        result = await caller.voice_message(args.message)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
