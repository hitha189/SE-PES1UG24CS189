"""
collisions: puck-vs-paddle collision handling.

Fixes over the original version:
  * Swept (continuous) detection  -> a fast puck can no longer tunnel through.
  * Push-out on contact           -> the puck can never stay inside a paddle.
  * Reflection about the contact normal (centre-to-centre line), so the
    rebound angle depends on WHERE the puck hits the paddle.
  * Paddle velocity is measured and added to the puck's rebound.
  * Velocity is only reflected if the puck is moving INTO the paddle, which
    removes the flip-flop that made the puck vibrate in place.

Assumptions about the game loop (once per frame, per paddle):
    paddles move -> puck.move() -> puck.bounce_off_walls() -> handle_paddle_collision()
"""

import math

RESTITUTION = 0.9        # 1.0 = perfectly elastic, lower = deader bounce
MAX_PUCK_SPEED = 20.0    # keeps the puck controllable after a hard hit
MAX_PADDLE_SPEED = 30.0  # larger per-frame jumps are treated as a teleport
SEPARATION_EPS = 0.5     # tiny gap left after push-out to avoid re-touching


def _paddle_motion(paddle):
    """Return (prev_x, prev_y, vx, vy) for the paddle this frame, derived from
    how far it moved since the last time this function saw it."""
    prev_x = getattr(paddle, "_last_x", paddle.x)
    prev_y = getattr(paddle, "_last_y", paddle.y)
    vx = paddle.x - prev_x
    vy = paddle.y - prev_y

    # A huge jump means the paddle was repositioned (e.g. restart), not swung.
    if math.hypot(vx, vy) > MAX_PADDLE_SPEED:
        prev_x, prev_y, vx, vy = paddle.x, paddle.y, 0.0, 0.0

    # Remember where the paddle is for the next frame.
    paddle._last_x = paddle.x
    paddle._last_y = paddle.y
    return prev_x, prev_y, vx, vy


def handle_paddle_collision(puck, paddle):
    """
    If the puck touched the paddle during this frame, push it out and
    rebound it. Returns True if a collision was handled this frame.
    """
    pad_x0, pad_y0, pad_vx, pad_vy = _paddle_motion(paddle)

    reach = puck.radius + paddle.radius

    # Where the puck was at the start of the frame.
    puck_x0 = puck.x - puck.vx
    puck_y0 = puck.y - puck.vy

    # Work in the paddle's frame: relative start position and relative motion.
    rel_x0 = puck_x0 - pad_x0
    rel_y0 = puck_y0 - pad_y0
    move_x = puck.vx - pad_vx
    move_y = puck.vy - pad_vy

    # Solve |rel0 + t * move| = reach for the first t in [0, 1].
    a = move_x * move_x + move_y * move_y
    b = rel_x0 * move_x + rel_y0 * move_y
    c = rel_x0 * rel_x0 + rel_y0 * rel_y0 - reach * reach

    end_x = puck.x - paddle.x
    end_y = puck.y - paddle.y
    end_dist = math.hypot(end_x, end_y)

    hit_t = None
    if c <= 0:
        hit_t = 0.0                          # already overlapping at frame start
    elif a > 1e-12:
        disc = b * b - a * c
        if disc >= 0:
            t = (-b - math.sqrt(disc)) / a
            if 0.0 <= t <= 1.0:
                hit_t = t
    if hit_t is None and end_dist < reach:
        hit_t = 1.0                          # numerical safety net

    if hit_t is None:
        return False

    # Contact normal: from paddle centre towards puck centre at the moment of impact.
    if c <= 0 and end_dist > 1e-6:
        nx, ny = end_x / end_dist, end_y / end_dist
    else:
        cx = rel_x0 + hit_t * move_x
        cy = rel_y0 + hit_t * move_y
        length = math.hypot(cx, cy)
        if length > 1e-6:
            nx, ny = cx / length, cy / length
        else:                                # dead-centre overlap: pick any sane direction
            speed = math.hypot(move_x, move_y)
            nx, ny = (-move_x / speed, -move_y / speed) if speed > 1e-6 else (1.0, 0.0)

    # 1) Push the puck out so it sits just outside the paddle.
    puck.x = paddle.x + nx * (reach + SEPARATION_EPS)
    puck.y = paddle.y + ny * (reach + SEPARATION_EPS)

    # 2) Reflect the puck's velocity *relative to the paddle*, only if it is
    #    moving into the paddle. This keeps angle-of-hit and paddle motion.
    rel_vx = puck.vx - pad_vx
    rel_vy = puck.vy - pad_vy
    approach = rel_vx * nx + rel_vy * ny
    if approach < 0:
        rel_vx -= (1.0 + RESTITUTION) * approach * nx
        rel_vy -= (1.0 + RESTITUTION) * approach * ny

    puck.vx = rel_vx + pad_vx
    puck.vy = rel_vy + pad_vy

    # 3) Cap the speed.
    speed = math.hypot(puck.vx, puck.vy)
    if speed > MAX_PUCK_SPEED:
        scale = MAX_PUCK_SPEED / speed
        puck.vx *= scale
        puck.vy *= scale

    return True