import reflex as rx


TOUR_SCROLL_SCRIPT = """
(() => {
    window.gahTourScrollCleanup?.();
    const name = __TARGET__;
    let timer = 0, stopped = false, attempts = 0;
    const cleanup = () => {
        stopped = true;
        clearTimeout(timer);
        if (window.gahTourScrollCleanup === cleanup) delete window.gahTourScrollCleanup;
    };
    window.gahTourScrollCleanup = cleanup;
    const scroll = () => {
        if (stopped) return;
        const card = document.getElementById('gah-tour-card');
        if (card && card.dataset.tourFocus !== name) { cleanup(); return; }
        const target = Array.from(document.querySelectorAll('[data-tour-target]'))
            .find(el => el.dataset.tourTarget === name && el.getClientRects().length);
        if (!card || !target) {
            if (++attempts < 30) timer = setTimeout(scroll, 100);
            else cleanup();
            return;
        }
        document.querySelectorAll('.gah-member-section, .gah-member-section [class*="overflow-y-auto"]')
            .forEach(el => el.scrollTo({top: 0, behavior: 'instant'}));
        target.scrollIntoView({block: 'start', behavior: 'instant'});
        window.dispatchEvent(new Event('resize'));
        cleanup();
    };
    timer = setTimeout(scroll, 100);
})();
"""


TOUR_POINTER_SCRIPT = """
(() => {
    window.gahTourPointerCleanup?.();
    const svg = document.getElementById('gah-tour-pointer');
    if (!svg) return;
    const line = svg.querySelector('line');
    const head = svg.querySelector('polyline');
    let frame = 0, stopped = false;
    let observedCard = null, observedTarget = null;
    const visible = (el) => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden';
    };
    const resize = new ResizeObserver(() => schedule());
    const measure = () => {
        frame = 0;
        if (stopped) return;
        svg.setAttribute('visibility', 'hidden');
        const card = document.getElementById('gah-tour-card');
        if (!card) return;
        const name = card.dataset.tourFocus;
        const target = Array.from(document.querySelectorAll('[data-tour-target]'))
            .find(el => el.dataset.tourTarget === name && visible(el));
        if (card !== observedCard || target !== observedTarget) {
            resize.disconnect();
            resize.observe(card);
            if (target) resize.observe(target);
            observedCard = card; observedTarget = target;
        }
        if (!target) return;
        const c = card.getBoundingClientRect(), t = target.getBoundingClientRect();
        const left = Math.max(0, t.left), right = Math.min(innerWidth, t.right);
        const top = Math.max(0, t.top), bottom = Math.min(innerHeight, t.bottom);
        if (left >= right || top >= bottom) return;
        const cx = c.left + c.width / 2, cy = c.top + c.height / 2;
        const tx = (left + right) / 2, ty = (top + bottom) / 2;
        const dx = tx - cx, dy = ty - cy, length = Math.hypot(dx, dy);
        if (!length) return;
        const start = Math.min((c.width / 2 + 3) / Math.abs(dx), (c.height / 2 + 3) / Math.abs(dy));
        const end = 1 - Math.min((right - left) / 2 / Math.abs(dx), (bottom - top) / 2 / Math.abs(dy));
        if (end <= start || (end - start) * length < 12) return;
        const x1 = cx + dx * start, y1 = cy + dy * start;
        const x2 = cx + dx * end, y2 = cy + dy * end;
        line.setAttribute('x1', x1); line.setAttribute('y1', y1);
        line.setAttribute('x2', x2); line.setAttribute('y2', y2);
        const ux = dx / length, uy = dy / length;
        head.setAttribute('points', `${x2 - 8*ux + 4*uy},${y2 - 8*uy - 4*ux} ${x2},${y2} ${x2 - 8*ux - 4*uy},${y2 - 8*uy + 4*ux}`);
        svg.setAttribute('visibility', 'visible');
    };
    const schedule = () => {
        if (!stopped && !frame) frame = requestAnimationFrame(measure);
    };
    const observer = new MutationObserver(schedule);
    observer.observe(document.body, {childList: true, subtree: true, attributes: true,
        attributeFilter: ['data-tour-focus', 'data-tour-target', 'class']});
    window.addEventListener('resize', schedule);
    document.addEventListener('scroll', schedule, true);
    window.visualViewport?.addEventListener('resize', schedule);
    window.visualViewport?.addEventListener('scroll', schedule);
    // No transitions or animation: the pointer also respects reduced motion.
    const cleanup = () => {
        stopped = true;
        cancelAnimationFrame(frame);
        observer.disconnect(); resize.disconnect();
        window.removeEventListener('resize', schedule);
        document.removeEventListener('scroll', schedule, true);
        window.visualViewport?.removeEventListener('resize', schedule);
        window.visualViewport?.removeEventListener('scroll', schedule);
        if (window.gahTourPointerCleanup === cleanup) delete window.gahTourPointerCleanup;
    };
    window.gahTourPointerCleanup = cleanup;
    schedule();
})();
"""


def tour_pointer() -> rx.Component:
    return rx.el.svg(
        rx.el.line(stroke="#e08b12", stroke_width="1.5"),
        rx.el.svg.polyline(fill="none", stroke="#e08b12", stroke_width="1.5"),
        id="gah-tour-pointer",
        aria_hidden="true",
        visibility="hidden",
        on_mount=rx.call_script(TOUR_POINTER_SCRIPT),
        on_unmount=rx.call_script(
            "window.gahTourPointerCleanup?.(); window.gahTourScrollCleanup?.();"
        ),
        class_name="pointer-events-none fixed inset-0 z-[69] h-dvh w-full overflow-visible",
    )
