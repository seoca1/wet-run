/** Audio module public API — unified exports for BGM and SFX playback.
 *
 * Re-exports the AudioManager singleton interface as functional entry points.
 * Consumers should import from this module rather than manager.ts directly.
 *
 * BGM (Background Music):
 * - playBgm(track?) — Begin playback of specified BGM track
 * - stopBgm() — Stop BGM playback
 * - getBgmVolume() / setBgmVolume(v) — BGM volume control (0..1)
 *
 * SFX (Sound Effects):
 * - playSfx(id?) — Play one-shot sound effect
 * - stopAllSfx() — Stop all active SFX
 * - getSfxVolume() / setSfxVolume(v) — SFX volume control (0..1)
 *
 * Global Controls:
 * - toggleMute() — Toggle mute for all audio
 * - isMuted() — Check current mute state
 * - unlockAudio() — Browser audio unlock (call on first user gesture)
 */

import { AudioManager } from "./manager.ts";
import type { SoundId, SoundEffectId } from "./manager.ts";

export { BGM_IDS, SFX_IDS } from "./manager.ts";
export type { SoundId, SoundEffectId };

function getManager(): AudioManager {
  return AudioManager.getInstance();
}

export function playBgm(track?: SoundId): void {
  getManager().play(track);
}

export function stopBgm(): void {
  getManager().stop();
}

export function getBgmVolume(): number {
  return getManager().getBgmVolume();
}

export function setBgmVolume(volume: number): void {
  getManager().setBgmVolume(volume);
}

export function playSfx(id?: SoundEffectId): void {
  getManager().playSfx(id);
}

export function stopAllSfx(): void {
  getManager().stopAllSfx();
}

export function getSfxVolume(): number {
  return getManager().getSfxVolume();
}

export function setSfxVolume(volume: number): void {
  getManager().setSfxVolume(volume);
}

export function toggleMute(): boolean {
  return getManager().toggleMute();
}

export function isMuted(): boolean {
  return getManager().isMuted();
}

export function unlockAudio(onUnlock?: () => void): void {
  AudioManager.unlockOnFirstGesture(onUnlock);
}

export function playBgmForEvent(event: string): string | null {
  return getManager().playBgmForEvent(event);
}

export function playPhase(phase: string): void {
  getManager().playPhase(phase);
}

export function isPlaying(): boolean {
  return getManager().isPlaying();
}

export function getCurrentTrack(): SoundId | null {
  return getManager().getCurrentTrack();
}

export function crossfadeTo(track: SoundId, durationMs?: number): void {
  getManager().crossfadeTo(track, durationMs);
}

export function fadeOutAndStop(durationMs?: number): void {
  getManager().fadeOutAndStop(durationMs);
}
