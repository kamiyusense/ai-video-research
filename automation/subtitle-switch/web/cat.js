/* Pure animation/interaction rules shared by the page and model-free Node tests. */
const CatMotion = (() => {
  function direction(dx, dy) {
    return (Math.round(Math.atan2(dy, dx) / (Math.PI / 4)) + 8) % 8;
  }
  function frameAt(spec, elapsed) {
    const index = Math.floor(Math.max(0, elapsed) * spec.fps / 1000);
    return spec.loop ? index % spec.frames : Math.min(index, spec.frames - 1);
  }
  function bodyOffset(elapsed, width, reduced = false) {
    return reduced ? 0 : (Math.max(0, elapsed) * .014) % (width + 144) - 144;
  }
  class Play {
    constructor(manifest) {
      this.manifest = manifest;
      this.lastNear = -Infinity;
      this.lastPunch = -Infinity;
      this.attack = null;
      this.look = 2;
    }
    pointer(dx, dy, now) {
      if (!this.manifest) return;
      const distance = Math.hypot(dx, dy);
      if (distance > 220) return;
      this.lastNear = now;
      this.look = direction(dx, dy);
      const cooldown = (this.manifest.punch_cooldown_sec ?? .6) * 1000;
      const current = this.attack && this.manifest[this.attack];
      const playing = current && now - this.lastPunch < current.frames / current.fps * 1000;
      if (distance <= (this.manifest.punch_radius_px ?? 70) && !playing && now - this.lastPunch >= cooldown) {
        this.attack = dx < 0 ? 'punch_left' : 'punch_right';
        this.lastPunch = now;
      }
    }
    sample(now) {
      if (!this.manifest) return null;
      const spec = this.attack && this.manifest[this.attack];
      if (spec && now - this.lastPunch < spec.frames / spec.fps * 1000) {
        return {group: this.attack, index: frameAt({...spec, loop: false}, now - this.lastPunch)};
      }
      return now - this.lastNear < 3000 ? {group: 'look', index: this.look} : null;
    }
  }
  return {direction, frameAt, bodyOffset, Play};
})();
if (typeof module !== 'undefined') module.exports = CatMotion;
